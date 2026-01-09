import logging

from homeassistant.core import HomeAssistant, callback
from homeassistant.const import (
    REVOLUTIONS_PER_MINUTE,
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS,
    LIGHT_LUX,
    UnitOfPower,
    UnitOfTemperature,
    EntityCategory,
    UnitOfVolumeFlowRate,
    UnitOfPressure,
    UnitOfTime,
)
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.components.sensor import SensorEntity
from homeassistant.components.sensor.const import SensorStateClass, SensorDeviceClass

from . import ActronAirNimbusConfigEntry
from .entity import ActronAirNimbusEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ActronAirNimbusConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the ActronAir Nimbus integration from a config entry."""
    coordinator = config_entry.runtime_data
    entities: list[ActronAirNimbusSensorEntity] = []

    for ac_serial, state in coordinator.data.items():
        entities.extend(
            [
                ActronAirNimbusCompressorSpeedSensor(coordinator, state, ac_serial),
                ActronAirNimbusCompressorModeSensor(coordinator, state, ac_serial),
                ActronAirNimbusCompressorPowerSensor(coordinator, state, ac_serial),
                ActronAirNimbusIndoorFanPwmSensor(coordinator, state, ac_serial),
                ActronAirNimbusIndoorFanRpmSensor(coordinator, state, ac_serial),
                ActronAirNimbusCompressorCoilTemperatureSensor(
                    coordinator, state, ac_serial
                ),
                ActronAirNimbusCompressorCoilInletTemperatureSensor(
                    coordinator, state, ac_serial
                ),
                ActronAirNimbusCompressorDischargeTemperatureSensor(
                    coordinator, state, ac_serial
                ),
                ActronAirNimbusVftAirflowSensor(coordinator, state, ac_serial),
                ActronAirNimbusVftStaticPressureSensor(coordinator, state, ac_serial),
            ]
        )

        # Add zone sensor entities for each existing zone
        for zone_id, zone in enumerate(state.zones):
            if not zone["NV_Exists"]:
                continue

            entities.extend(
                [
                    ActronAirNimbusZoneSensorBatterySensor(
                        coordinator, state, ac_serial, zone_id
                    ),
                    ActronAirNimbusZoneSensorWifiSignalStrengthSensor(
                        coordinator, state, ac_serial, zone_id
                    ),
                    ActronAirNimbusZoneDamperPositionSensor(
                        coordinator, state, ac_serial, zone_id
                    ),
                ]
            )

    async_add_entities(entities)


class ActronAirNimbusSensorEntity(ActronAirNimbusEntity, SensorEntity):
    """Base class for ActronAir Nimbus sensor entities."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, initial_state, ac_serial: str) -> None:
        super().__init__(coordinator, ac_serial)
        self.ac_serial = ac_serial

        self._attr_unique_id = f"{ac_serial}_{self._attr_translation_key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, ac_serial)},
        }

        self._update_internal_state(initial_state)

    @callback
    def _handle_coordinator_update(self) -> None:
        state = self.coordinator.data[self.ac_serial]

        self._update_internal_state(state)

        return super()._handle_coordinator_update()


class ActronAirNimbusZoneSensorEntity(ActronAirNimbusEntity, SensorEntity):
    """Base class for ActronAir Nimbus sensor entities."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self, coordinator, initial_state, ac_serial: str, zone_id: str
    ) -> None:
        super().__init__(coordinator, ac_serial)
        self.ac_serial = ac_serial
        self.zone_id = zone_id

        self._attr_unique_id = (
            f"{ac_serial}_zone_{zone_id}_{self._attr_translation_key}"
        )
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"{ac_serial}_zone_{zone_id}")},
        }

        self._update_internal_state(initial_state)

    @callback
    def _handle_coordinator_update(self) -> None:
        state = self.coordinator.data[self.ac_serial]

        self._update_internal_state(state)

        return super()._handle_coordinator_update()


class ActronAirNimbusCompressorSpeedSensor(ActronAirNimbusSensorEntity):
    """Representation of the compressor speed sensor."""

    _attr_translation_key = "compressor_speed"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE

    def _update_internal_state(self, state):
        """Update the internal state from the coordinator data."""
        self._attr_native_value = state._state["LiveAircon"]["OutdoorUnit"]["CompSpeed"]


class ActronAirNimbusCompressorModeSensor(ActronAirNimbusSensorEntity):
    """Representation of the compressor mode sensor."""

    _attr_translation_key = "compressor_mode"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["OFF", "HEAT", "COOL"]

    def _update_internal_state(self, state):
        """Update the internal state from the coordinator data."""
        self._attr_native_value = state._state["LiveAircon"]["CompressorMode"]


class ActronAirNimbusCompressorPowerSensor(ActronAirNimbusSensorEntity):
    """Representation of the compressor power sensor."""

    _attr_translation_key = "compressor_power"
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfPower.WATT

    def _update_internal_state(self, state):
        """Update the internal state from the coordinator data."""
        self._attr_native_value = state._state["LiveAircon"]["OutdoorUnit"]["CompPower"]


class ActronAirNimbusIndoorFanPwmSensor(ActronAirNimbusSensorEntity):
    """Representation of the indoor fan PWM sensor."""

    _attr_translation_key = "indoor_fan_pwm"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE

    def _update_internal_state(self, state):
        """Update the internal state from the coordinator data."""
        self._attr_native_value = state._state["LiveAircon"]["FanPWM"]


class ActronAirNimbusIndoorFanRpmSensor(ActronAirNimbusSensorEntity):
    """Representation of the indoor fan RPM sensor."""

    _attr_translation_key = "indoor_fan_rpm"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = REVOLUTIONS_PER_MINUTE

    def _update_internal_state(self, state):
        """Update the internal state from the coordinator data."""
        self._attr_native_value = state._state["LiveAircon"]["FanRPM"]


class ActronAirNimbusCompressorCoilTemperatureSensor(ActronAirNimbusSensorEntity):
    """Representation of the compressor coil temperature sensor."""

    _attr_translation_key = "compressor_coil_temperature"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def _update_internal_state(self, state):
        """Update the internal state from the coordinator data."""
        self._attr_native_value = state._state["LiveAircon"]["OutdoorUnit"]["CoilTemp"]


class ActronAirNimbusCompressorCoilInletTemperatureSensor(ActronAirNimbusSensorEntity):
    """Representation of the compressor coil inlet temperature sensor."""

    _attr_translation_key = "compressor_coil_inlet_temperature"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def _update_internal_state(self, state):
        """Update the internal state from the coordinator data."""
        self._attr_native_value = state._state["LiveAircon"]["CoilInlet"]


class ActronAirNimbusCompressorCoilInletTemperatureSensor(ActronAirNimbusSensorEntity):
    """Representation of the compressor coil inlet temperature sensor."""

    _attr_translation_key = "compressor_coil_inlet_temperature"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def _update_internal_state(self, state):
        """Update the internal state from the coordinator data."""
        self._attr_native_value = state._state["LiveAircon"]["DischargeTemp"]


class ActronAirNimbusVftAirflowSensor(ActronAirNimbusSensorEntity):
    """Representation of the VFT airflow sensor."""

    _attr_translation_key = "vft_airflow"
    _attr_device_class = SensorDeviceClass.VOLUME_FLOW_RATE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfVolumeFlowRate.LITERS_PER_SECOND

    def _update_internal_state(self, state):
        """Update the internal state from the coordinator data."""
        self._attr_native_value = state._state["UserAirconSettings"]["VFT"]["Airflow"]


class ActronAirNimbusVftStaticPressureSensor(ActronAirNimbusSensorEntity):
    """Representation of the VFT static pressure sensor."""

    _attr_translation_key = "vft_static_pressure"
    _attr_device_class = SensorDeviceClass.PRESSURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfPressure.PA

    def _update_internal_state(self, state):
        """Update the internal state from the coordinator data."""
        self._attr_native_value = state._state["UserAirconSettings"]["VFT"][
            "StaticPressure"
        ]


class ActronAirNimbusWifiSignalStrengthSensor(ActronAirNimbusSensorEntity):
    """Representation of the WiFi signal strength sensor."""

    _attr_translation_key = "wifi_signal_strength"
    _attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = SIGNAL_STRENGTH_DECIBELS

    def _update_internal_state(self, state):
        """Update the internal state from the coordinator data."""
        self._attr_native_value = state._state[f"<{self.ac_serial.upper()}>"][
            "SystemStatus_Local"
        ]["WifiStrength_of3"]


class ActronAirNimbusZoneSensorBatterySensor(ActronAirNimbusZoneSensorEntity):
    """Representation of the zone sensor battery sensor."""

    _attr_translation_key = "zone_sensor_battery"
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE

    def _update_internal_state(self, state):
        """Update the internal state from the coordinator data."""
        peripherals = [
            peripheral
            for peripheral in state._state["AirconSystem"]["Peripherals"]
            if peripheral["DeviceType"] == "Zone Sensor"
        ]
        peripherals.sort(key=lambda x: x["ZoneAssignment"][0])

        self._attr_native_value = peripherals[self.zone_id][
            "RemainingBatteryCapacity_pc"
        ]


class ActronAirNimbusZoneSensorWifiSignalStrengthSensor(ActronAirNimbusZoneSensorEntity):
    """Representation of the zone sensor wifi signal strength sensor."""

    _attr_translation_key = "zone_sensor_wifi_signal_strength"
    _attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = SIGNAL_STRENGTH_DECIBELS

    def _update_internal_state(self, state):
        """Update the internal state from the coordinator data."""
        self._attr_native_value = state.zones[self.zone_id]["Sensors"][self.ac_serial.upper()]["Signal_of3"]


class ActronAirNimbusZoneDamperPositionSensor(ActronAirNimbusZoneSensorEntity):
    """Representation of the zone damper position sensor."""

    _attr_translation_key = "zone_damper_position"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE

    def _update_internal_state(self, state):
        """Update the internal state from the coordinator data."""
        # this appears to be a value out of 20. Convert to a real
        self._attr_native_value = 100 * state.zones[self.zone_id]["ZonePosition"] / 20
