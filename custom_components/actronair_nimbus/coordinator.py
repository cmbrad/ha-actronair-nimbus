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

    async def _async_setup(self):
        _LOGGER.debug("Fetching systems")
        self.systems = await self.actron_api_client.get_ac_systems()

    async def _async_update_data(self) -> dict:
        """Fetch updates and merge incremental changes into the full state."""

        _LOGGER.debug("Performing data update")

        # take a copy - update all or nothing
        data = copy.deepcopy(self.data) if self.data is not None else {}

        try:
            for system in self.systems["_embedded"]["ac-system"]:
                serial_number = system["serial"]

                # initialise to empty state if we've not seen anything
                if serial_number not in data:
                    data[serial_number] = ActronAdvanceState()

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
        except Exception as e:
            _LOGGER.exception("Failed to update data")
            raise UpdateFailed("Failed to update data") from e

        _LOGGER.debug("Data update complete")

        return data
