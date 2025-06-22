from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
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
        entities.append(QuiteModeActiveBinarySensor(coordinator, state, unique_id))

    async_add_entities(entities)


class QuiteModeActiveBinarySensor(ActronAirNimbusEntity, BinarySensorEntity):
    """Representation of an Actron Air Nimbus binary sensor."""

    _attr_translation_key = "quite_mode_active"
    _attr_device_class = BinarySensorDeviceClass.RUNNING

    def __init__(
        self,
        coordinator,
        initial_state,
        ac_serial: str,
    ) -> None:
        super().__init__(coordinator, ac_serial)

        self.ac_serial = ac_serial

        self._attr_unique_id = f"{ac_serial}_{self._attr_translation_key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, ac_serial)},
        )

    @property
    def is_on(self) -> bool:
        """Return True if the binary sensor is on."""
        return self.coordinator.data[self.ac_serial]._state["UserAirconSettings"][
            "QuietModeActive"
        ]
