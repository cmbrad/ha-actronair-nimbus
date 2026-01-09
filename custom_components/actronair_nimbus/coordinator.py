import copy
import logging

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.components.climate import SCAN_INTERVAL
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.debounce import Debouncer

from .const import DOMAIN

from .api.data import ActronAdvanceState

_LOGGER = logging.getLogger(__name__)

type ActronAirNimbusConfigEntry = ConfigEntry[ActronAirNimbusDataUpdateCoordinator]
REQUEST_REFRESH_DELAY = (
    10.0  # seconds to wait before allowing another request to refresh data
)

DATA_MODE_EVENT = "event"
DATA_MODE_STATUS = "status"


class ActronAirNimbusDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the ActronAir Nimbus device."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ActronAirNimbusConfigEntry,
        actron_api_client,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
            # customise debouncer and always update to fix UI responsiveness
            request_refresh_debouncer=Debouncer(
                hass, _LOGGER, cooldown=REQUEST_REFRESH_DELAY, immediate=False
            ),
            always_update=True,
        )

        self.actron_api_client = actron_api_client

        self.systems = None

        self.data_mode = DATA_MODE_STATUS

        self.servicing = None

    async def _async_setup(self):
        _LOGGER.debug("Fetching systems")
        self.systems = await self.actron_api_client.get_ac_systems()

    async def _async_update_data(self) -> dict:
        """Fetch updates and merge incremental changes into the full state."""

        _LOGGER.debug(f"Performing data update using mode {self.data_mode}")

        # take a copy - update all or nothing
        data = copy.deepcopy(self.data) if self.data is not None else {}

        try:
            for system in self.systems["_embedded"]["ac-system"]:
                serial_number = system["serial"]

                # initialise to empty state if we've not seen anything
                if serial_number not in data:
                    data[serial_number] = ActronAdvanceState()

                if self.data_mode == DATA_MODE_STATUS:
                    await self._async_update_status(
                        serial_number=serial_number, data=data
                    )
                if self.data_mode == DATA_MODE_EVENT:
                    await self._async_update_event(
                        serial_number=serial_number, data=data
                    )

        except Exception as e:
            _LOGGER.exception("Failed to update data")
            raise UpdateFailed("Failed to update data") from e

        _LOGGER.debug("Data update complete")

        _LOGGER.debug('Determining if need to raise alerts')

        # "Servicing": {
        #         "NV_ErrorHistory": [
        #             {
        #                 "Code": "E00",
        #                 "Description": "No Error",
        #                 "Severity": "No Error",
        #                 "Time": "2026-01-09T17:17:51"
        #             },
        #             {
        #                 "Code": "E06",
        #                 "Description": "High Discharge Temp. (Discharge Temp exceeded 138C)",
        #                 "Severity": "Error",
        #                 "Time": "2026-01-09T17:17:01"
        #             },
        #             {
        #                 "Code": "E00",
        #                 "Description": "No Error",
        #                 "Severity": "No Error",
        #                 "Time": "2026-01-09T16:45:16"
        #             },
        #             {
        #                 "Code": "E06",
        #                 "Description": "High Discharge Temp. (Discharge Temp exceeded 138C)",
        #                 "Severity": "Error",
        #                 "Time": "2026-01-09T16:44:43"
        #             }
        #         ]
        # }

        for error in data.get('Servicing', {}).get('NV_ErrorHistory', []):
            # if we haven't seen any errors before, stop! We don't want to flood on past errors
            if self.servicing is None:
                _LOGGER.debug('No prior servicing data, skipping alert raising to avoid flood')
                break
            # if we have seen an error before - stop! The API returns the latest error first, so we can skip the rest
            if error in self.servicing.get('NV_ErrorHistory', []):
                _LOGGER.debug(f'Seen error ({error}) before, stopping alert raising to avoid duplicates')
                break
            # if an error is not an error, skip it
            if error['Severity'] == 'No Error':
                continue

            _LOGGER.debug(f'Raising alert for ActronAir Nimbus error: {error}')
            create_notification(self.hass, f"{error['Description']} (Severity: {error['Severity']}, Code: {error['Code']}, Time: {error['Time']})", title="ActronAir Nimbus Alert")


        # save servicing data so we know what errors we have seen so far
        self.servicing = copy.deepcopy(data.get('Servicing', {}))
        _LOGGER.debug('Alert raising complete, saved servicing data')

        return data

    async def _async_update_status(self, serial_number: str, data: dict) -> dict:
        data[serial_number].update_from_status(
            status=await self.actron_api_client.get_ac_status(serial=serial_number)
        )

    async def _async_update_event(self, serial_number: str, data: dict) -> dict:
        # if the state is empty then get all events, otherwise just get latest
        # that we have not seen yet
        if data[serial_number]._event_id is None:
            _LOGGER.debug('Getting latest events for "%s"', serial_number)
            events = await self.actron_api_client.get_ac_events(
                serial=serial_number, event_type="latest"
            )
        else:
            _LOGGER.debug(
                'Getting newer events for "%s" since event id %s',
                serial_number,
                data[serial_number]._event_id,
            )
            events = await self.actron_api_client.get_ac_events(
                serial=serial_number,
                event_type="newer",
                event_id=data[serial_number]._event_id,
            )
            _LOGGER.debug(
                'Found %d newer events for "%s"',
                len(events["events"]),
                serial_number,
            )

        # ensure sorted so that we apply oldest to newest or result will be wrong
        for event in sorted(events["events"], key=lambda x: x["timestamp"]):
            data[serial_number].update_from_event(event)
