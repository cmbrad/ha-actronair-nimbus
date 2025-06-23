"""The Actron Air Nimbus integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    Platform,
    CONF_HOST,
    CONF_PASSWORD,
    CONF_USERNAME,
    CONF_API_TOKEN,
)
from homeassistant.core import HomeAssistant

from .coordinator import ActronAirNimbusDataUpdateCoordinator
from .api.adapter import APIAdapter
from .api.client import ActronAirAPIClient
from .api.data import ActronAdvanceState

# TODO List the platforms that you want to support.
# For your initial PR, limit it to 1 platform.
_PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.CLIMATE,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.UPDATE,
]

# TODO Create ConfigEntry type alias with API object
# TODO Rename type alias and update all entry annotations
type ActronAirNimbusConfigEntry = ConfigEntry[ActronAirNimbusDataUpdateCoordinator]


# TODO Update entry annotation
async def async_setup_entry(
    hass: HomeAssistant, entry: ActronAirNimbusConfigEntry
) -> bool:
    """Set up Actron Air Nimbus from a config entry."""

    # TODO 1. Create API instance
    # TODO 2. Validate the API connection (and authentication)
    # TODO 3. Store an API object for your platforms to access
    # entry.runtime_data = MyAPI(...)
    # actron_api_client = ActronAirNimbusApiClient(
    #     host=entry.data[CONF_HOST],
    #     username=entry.data[CONF_USERNAME],
    #     password=entry.data[CONF_PASSWORD],
    # )
    actron_api_adapter = APIAdapter(max_attempts=5)
    actron_api_client = ActronAirAPIClient(
        adapter=actron_api_adapter, pairing_token=entry.data[CONF_API_TOKEN]
    )

    coordinator = ActronAirNimbusDataUpdateCoordinator(
        hass=hass,
        config_entry=entry,
        actron_api_client=actron_api_client,
    )
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)

    return True


# TODO Update entry annotation
async def async_unload_entry(
    hass: HomeAssistant, entry: ActronAirNimbusConfigEntry
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)
