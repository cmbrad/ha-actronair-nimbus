import asyncio
import logging

from datetime import datetime, timedelta
from typing import List

from .adapter import APIAdapter

# Configure logging
logger = logging.getLogger(__name__)


class ActronAirAPIClient:
    BASE_URL = 'https://nimbus.actronair.com.au'

    TOKEN_EXPIRATION_LEEWAY_SECONDS = 60


    def __init__(self, adapter: APIAdapter, pairing_token: str):
        self.adapter = adapter

        self.pairing_token = pairing_token

        self.access_token = None
        self.token_expiration_timestamp = None

    async def refresh_access_token(self):
        url = f"{self.BASE_URL}/api/v0/oauth/token"
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": self.pairing_token,
            "client_id": "app",
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }

        response = await self.adapter.request(method='POST', url=url, data=payload, headers=headers)
        if response is not None:
            data = await response.json()
            self.access_token = data["access_token"]
            expires_in = data["expires_in"]
            self.token_expiration_timestamp = datetime.utcnow() + timedelta(seconds=expires_in)
            logger.info(f"Access token refreshed successfully. Will expire at {self.token_expiration_timestamp} (in {expires_in} seconds)")
        else:
            logger.error("Failed to refresh access token")
            raise Exception("Failed to refresh access token")

    async def ensure_valid_token(self):
        # no token - refresh for first time
        if self.access_token is None:
            await self.refresh_access_token()

        now = datetime.utcnow()
        renew_at_timestamp = self.token_expiration_timestamp - timedelta(seconds=self.TOKEN_EXPIRATION_LEEWAY_SECONDS)
        seconds_until_renewal = int((renew_at_timestamp - now).total_seconds())
        logger.debug(f'Will renew token at {renew_at_timestamp} (in {seconds_until_renewal} seconds)')

        # token is due to expire, refresh it
        if now >= renew_at_timestamp:
            await self.refresh_access_token()

    async def request_pairing_token(self, username: str, password: str, client: str, device_name: str, device_unique_id: str):
        url = f"{self.BASE_URL}/api/v0/client/user-devices"
        payload = {
            "username": username,
            "password": password,
            "client": client,
            "deviceName": device_name,
            "deviceUniqueIdentifier": device_unique_id,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        response = await self.adapter.request(method='POST', url=url, data=payload, headers=headers)

        data = await response.json()
        return data["pairingToken"]

    async def get_ac_systems(self):
        return await self._request(method='GET', path='/api/v0/client/ac-systems?includeNeo=true')

    async def get_ac_events(self, serial: str, event_type: str = 'latest', event_id: str = None):
        if event_type == 'latest':
            path = f'/api/v0/client/ac-systems/events/latest?serial={serial}'
        elif event_type == 'newer':
            path = f'/api/v0/client/ac-systems/events/newer?serial={serial}&newerThanEventId={event_id}'
        elif event_type == 'older':
            path = f'/api/v0/client/ac-systems/events/older?serial={serial}&olderThanEventId={event_id}'
        else:
            raise ValueError(f"Invalid event type: {event_type}")

        return await self._request(method='GET', path=path)

    async def stream_ac_events(self, serial: str, refresh_secs: int = 15):
        latest_event_id = None
        while True:
            if latest_event_id is None:
                events_data = await self.get_ac_events(serial=serial)
            else:
                events_data = await self.get_ac_events(serial=serial, event_type='newer', event_id=latest_event_id)

            # sort from oldest to newest event (api defaults to newest->oldest)
            events = sorted(events_data['events'], key=lambda x: x['timestamp'])

            # remember latest event
            if len(events) > 0:
                latest_event_id = events[-1]['id']

            for event in events:
                yield event

            await asyncio.sleep(refresh_secs)

    async def get_ac_status(self, serial: str):
        return await self._request(method='GET', path=f'/api/v0/client/ac-systems/status/latest?serial={serial}')

    async def send_command(self, serial: str, command: dict):
        return await self._request(method='POST', path=f'/api/v0/client/ac-systems/cmds/send?serial={serial}', json=command)

    async def set_settings(self, serial: str, settings: dict):
        return await self.send_command(serial=serial, command={"command": ({"type": "set-settings"} | settings)})

    async def set_enabled_zones(self, serial: str, enabled_zones: List[bool]):
        return await self.set_settings(serial=serial, settings={'UserAirconSettings.EnabledZones': enabled_zones})

    async def set_system_mode(self, serial: str, mode: str = None, is_on: bool = None):
        # base settings
        settings = {}

        # API can either turn on/off, or set mode, or both at the same time
        if is_on is not None:
            settings['UserAirconSettings.isOn'] = is_on

        if mode is not None:
            settings['UserAirconSettings.Mode'] = mode

        return await self.set_settings(serial=serial, settings=settings)

    async def set_fan_mode(self, serial: str, mode: str, continuous: bool):
        if not mode.endswith('+CONT') and continuous:
            mode += '+CONT'
        return await self.set_settings(serial=serial, settings={"UserAirconSettings.FanMode": mode})

    async def set_temperature_setpoint(self, serial: str, cool: float, heat: float, zone_number: int):
        # base settings
        settings = {}

        if zone_number is None:
            if cool is not None:
                settings['UserAirconSettings.TemperatureSetpoint_Cool_oC'] = cool

            if heat is not None:
                settings['UserAirconSettings.TemperatureSetpoint_Heat_oC'] = heat
        else:
            if cool is not None:
                settings[f'RemoteZoneInfo[{zone_number}].TemperatureSetpoint_Cool_oC'] = cool
            if heat is not None:
                settings[f'RemoteZoneInfo[{zone_number}].TemperatureSetpoint_Heat_oC'] = heat

        return await self.set_settings(serial=serial, settings=settings)

    async def _request(self, method: str, path: str, *args, **kwargs):
        await self.ensure_valid_token()
        url = f"{self.BASE_URL}{path}"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = await self.adapter.request(method=method, url=url, headers=headers, *args, **kwargs)
        return await response.json()
