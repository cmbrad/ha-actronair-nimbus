from homeassistant.core import HomeAssistant, callback
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
        entities.extend(
            [
                ActronAirNimbusQuiteModeActiveBinarySensor(
                    coordinator, state, unique_id
                ),
                ActronAirNimbusCleanFilterAlertBinarySensor(
                    coordinator, state, unique_id
                ),
                ActronAirNimbusDefrostingAlertBinarySensor(
                    coordinator, state, unique_id
                ),
            ]
        )

        entities.extend(
            [
                ActronAirNimbusZoneSensorConnectedBinarySensor(
                    coordinator, state, unique_id, zone_id
                )
                for zone_id, zone in enumerate(state.zones)
                if zone["NV_Exists"]
            ]
        )

    async_add_entities(entities)


class ActronAirNimbusQuiteModeActiveBinarySensor(
    ActronAirNimbusEntity, BinarySensorEntity
):
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
        self._update_internal_state(initial_state)

    @callback
    def _handle_coordinator_update(self) -> None:
        state = self.coordinator.data[self.ac_serial]

        self._update_internal_state(state)

        return super()._handle_coordinator_update()

    def _update_internal_state(self, state):
        self._attr_is_on = state._state["UserAirconSettings"]["QuietModeActive"]


class ActronAirNimbusCleanFilterAlertBinarySensor(
    ActronAirNimbusEntity, BinarySensorEntity
):
    """Representation of an Actron Air Nimbus binary sensor."""

    _attr_translation_key = "clean_filter_alert"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

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

        self._update_internal_state(initial_state)

    @callback
    def _handle_coordinator_update(self) -> None:
        state = self.coordinator.data[self.ac_serial]

        self._update_internal_state(state)

        return super()._handle_coordinator_update()

    def _update_internal_state(self, state):
        """Update the internal state from the coordinator data."""
        self._attr_is_on = state._state["Alerts"]["CleanFilter"]


class ActronAirNimbusDefrostingAlertBinarySensor(
    ActronAirNimbusEntity, BinarySensorEntity
):
    """Representation of an Actron Air Nimbus binary sensor."""

    _attr_translation_key = "defrosting_alert"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

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

        self._update_internal_state(initial_state)

    @callback
    def _handle_coordinator_update(self) -> None:
        state = self.coordinator.data[self.ac_serial]

        self._update_internal_state(state)

        return super()._handle_coordinator_update()

    def _update_internal_state(self, state):
        """Update the internal state from the coordinator data."""
        self._attr_is_on = state._state["Alerts"]["Defrosting"]


class ActronAirNimbusZoneSensorConnectedBinarySensor(
    ActronAirNimbusEntity, BinarySensorEntity
):
    """Representation of an Actron Air Nimbus binary sensor."""

    _attr_translation_key = "zone_sensor_connected"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(
        self,
        coordinator,
        initial_state,
        ac_serial: str,
        zone_id: str,
    ) -> None:
        super().__init__(coordinator, ac_serial)

        self.ac_serial = ac_serial
        self.zone_id = zone_id

        self._attr_unique_id = (
            f"{ac_serial}_zone_{zone_id}_{self._attr_translation_key}"
        )
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{ac_serial}_zone_{zone_id}")},
        )

        self._update_internal_state(initial_state)

    @callback
    def _handle_coordinator_update(self) -> None:
        state = self.coordinator.data[self.ac_serial]

        self._update_internal_state(state)

        return super()._handle_coordinator_update()

    def _update_internal_state(self, state):
        """Update the internal state from the coordinator data."""
        peripherals = [
            peripheral
            for peripheral in state._state["AirconSystem"]["Peripherals"]
            if peripheral["DeviceType"] == "Zone Sensor"
        ]
        peripherals.sort(key=lambda x: x["ZoneAssignment"][0])

        self._attr_is_on = peripherals[self.zone_id]["ConnectionState"] == "Connected"
