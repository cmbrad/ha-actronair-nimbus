"""Use for firmware update status."""

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.components.update import UpdateEntity, UpdateDeviceClass
from homeassistant.helpers.device_registry import DeviceInfo

from . import ActronAirNimbusConfigEntry
from .const import DOMAIN
from .entity import ActronAirNimbusEntity


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ActronAirNimbusConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the ActronAir Nimbus integration from a config entry."""
    coordinator = config_entry.runtime_data
    entities: list[ActronAirNimbusEntity] = []

    for unique_id, state in coordinator.data.items():
        entities.extend(
            [
                ActronAirNimbusWallControllerFirmwareUpdate(
                    coordinator, state, unique_id
                ),
                ActronAirNimbusIndoorUnitFirmwareUpdate(coordinator, state, unique_id),
                ActronAirNimbusOutdoorUnitFirmwareUpdate(coordinator, state, unique_id),
            ]
        )

    async_add_entities(entities)


class ActronAirNimbusUpdateEntity(ActronAirNimbusEntity, UpdateEntity):
    """Base class for Actron Air Nimbus update entities."""

    _attr_auto_update = True
    _attr_device_class = UpdateDeviceClass.FIRMWARE

    def __init__(self, coordinator, initial_state, ac_serial: str) -> None:
        super().__init__(coordinator, ac_serial)
        self.ac_serial = ac_serial
        self._attr_unique_id = f"{ac_serial}_{self._attr_translation_key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, ac_serial)},
        )
        self._update_from_state(initial_state)

    def _update_from_state(self, state) -> None:
        """Update the entity with version information from the state."""
        version = self._get_version_from_state(state)
        self._attr_installed_version = version
        self._attr_latest_version = version

    def _get_version_from_state(self, state) -> str:
        """Extract the version from the state. Override in subclasses."""
        raise NotImplementedError

    def _handle_coordinator_update(self) -> None:
        """Handle updates from the coordinator."""
        state = self.coordinator.data[self.ac_serial]
        self._update_from_state(state)
        self.async_write_ha_state()


class ActronAirNimbusWallControllerFirmwareUpdate(ActronAirNimbusUpdateEntity):
    """Representation of a firmware update status for the wall controller."""

    _attr_translation_key = "wall_controller_firmware_update"

    def _get_version_from_state(self, state) -> str:
        """Extract the wall controller firmware version from the state."""
        return state._state["AirconSystem"]["MasterWCFirmwareVersion"]


class ActronAirNimbusIndoorUnitFirmwareUpdate(ActronAirNimbusUpdateEntity):
    """Representation of a firmware update status for the indoor unit."""

    _attr_translation_key = "indoor_unit_firmware_update"

    def _get_version_from_state(self, state) -> str:
        """Extract the indoor unit firmware version from the state."""
        return state._state["AirconSystem"]["IndoorUnit"]["IndoorFW"]


class ActronAirNimbusOutdoorUnitFirmwareUpdate(ActronAirNimbusUpdateEntity):
    """Representation of a firmware update status for the outdoor unit."""

    _attr_translation_key = "outdoor_unit_firmware_update"

    def _get_version_from_state(self, state) -> str:
        """Extract the outdoor unit firmware version from the state."""
        return state._state["AirconSystem"]["OutdoorUnit"]["SoftwareVersion"]
