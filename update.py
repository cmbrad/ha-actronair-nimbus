"""
Use for firmware update status
"""

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


class ActronAirNimbusWallControllerFirmwareUpdate(ActronAirNimbusEntity, UpdateEntity):
    """Representation of a firmware update status for the wall controller."""

    _attr_auto_update = True
    _attr_device_class = UpdateDeviceClass.FIRMWARE
    _attr_translation_key = "wall_controller_firmware_update"

    def __init__(self, coordinator, initial_state, ac_serial: str) -> None:
        super().__init__(coordinator, ac_serial)
        self.ac_serial = ac_serial

        self._attr_unique_id = f"{ac_serial}_{self._attr_translation_key}"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, ac_serial)},
        )

        self._attr_installed_version = initial_state._state["AirconSystem"][
            "MasterWCFirmwareVersion"
        ]
        self._attr_latest_version = initial_state._state["AirconSystem"][
            "MasterWCFirmwareVersion"
        ]


class ActronAirNimbusIndoorUnitFirmwareUpdate(ActronAirNimbusEntity, UpdateEntity):
    """Representation of a firmware update status for the indoor unit."""

    _attr_auto_update = True
    _attr_device_class = UpdateDeviceClass.FIRMWARE
    _attr_translation_key = "indoor_unit_firmware_update"

    def __init__(self, coordinator, initial_state, ac_serial: str) -> None:
        super().__init__(coordinator, ac_serial)
        self.ac_serial = ac_serial

        self._attr_unique_id = f"{ac_serial}_{self._attr_translation_key}"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, ac_serial)},
        )

        self._attr_installed_version = initial_state._state["AirconSystem"][
            "IndoorUnit"
        ]["IndoorFW"]
        self._attr_latest_version = initial_state._state["AirconSystem"]["IndoorUnit"][
            "IndoorFW"
        ]


class ActronAirNimbusOutdoorUnitFirmwareUpdate(ActronAirNimbusEntity, UpdateEntity):
    """Representation of a firmware update status for the outdoor unit."""

    _attr_auto_update = True
    _attr_device_class = UpdateDeviceClass.FIRMWARE
    _attr_translation_key = "outdoor_unit_firmware_update"

    def __init__(self, coordinator, initial_state, ac_serial: str) -> None:
        super().__init__(coordinator, ac_serial)
        self.ac_serial = ac_serial

        self._attr_unique_id = f"{ac_serial}_{self._attr_translation_key}"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, ac_serial)},
        )

        self._attr_installed_version = initial_state._state["AirconSystem"][
            "OutdoorUnit"
        ]["SoftwareVersion"]
        self._attr_latest_version = initial_state._state["AirconSystem"]["OutdoorUnit"][
            "SoftwareVersion"
        ]
