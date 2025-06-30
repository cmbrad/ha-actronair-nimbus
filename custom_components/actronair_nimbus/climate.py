import logging

from homeassistant.components.climate import (
    FAN_AUTO,
    FAN_HIGH,
    FAN_MEDIUM,
    FAN_LOW,
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
    HVACAction,
)
from homeassistant.const import (
    ATTR_TEMPERATURE,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo

from . import ActronAirNimbusConfigEntry
from .api.data import ActronAdvanceState
from .const import DOMAIN
from .entity import ActronAirNimbusEntity

_LOGGER = logging.getLogger(__name__)

HVAC_MODE_ACTRON_TO_HA = {
    "OFF": HVACMode.OFF,
    "HEAT": HVACMode.HEAT,
    "COOL": HVACMode.COOL,
    "AUTO": HVACMode.HEAT_COOL,
    "FAN_ONLY": HVACMode.FAN_ONLY,
}

HVAC_MODE_HA_TO_ACTRON = {
    HVACMode.OFF: "OFF",
    HVACMode.HEAT: "HEAT",
    HVACMode.COOL: "COOL",
    HVACMode.HEAT_COOL: "AUTO",
    HVACMode.FAN_ONLY: "FAN_ONLY",
}

FAN_MODE_ACTRON_TO_HA = {
    "AUTO": FAN_AUTO,
    "LOW": FAN_LOW,
    "MEDIUM": FAN_MEDIUM,
    "HIGH": FAN_HIGH,
}

FAN_MODE_HA_TO_ACTRON = {
    FAN_AUTO: "AUTO",
    FAN_LOW: "LOW",
    FAN_MEDIUM: "MEDIUM",
    FAN_HIGH: "HIGH",
}

HVAC_ACTION_ACTRON_TO_HA = {
    "HEAT": HVACAction.HEATING,
    "COOL": HVACAction.COOLING,
}

HVAC_ACTION_HA_TO_ACTRON = {
    HVACAction.HEATING: "HEAT",
    HVACAction.COOLING: "COOL",
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ActronAirNimbusConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Actron Air Nimbus climate entity."""
    coordinator = config_entry.runtime_data

    entities: list[ActronAirNimbusClimateEntity] = []

    for unique_id, state in coordinator.data.items():
        entities.append(
            ActronAirNimbusAirConditioner(
                coordinator=coordinator, initial_state=state, unique_id=unique_id
            )
        )

        entities.extend(
            [
                ActronAirNimbusZone(
                    coordinator=coordinator,
                    initial_state=state,
                    ac_serial=unique_id,
                    zone_id=i,
                )
                for i, zone in enumerate(state.zones)
                if zone["NV_Exists"]
            ]
        )

    async_add_entities(new_entities=entities)


class ActronAirNimbusClimateEntity(ActronAirNimbusEntity, ClimateEntity):
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_target_temperature_step = 0.5


class ActronAirNimbusAirConditioner(ActronAirNimbusClimateEntity):
    """Representation of an Actron Air Nimbus air conditioner."""

    _attr_hvac_modes = [
        HVACMode.OFF,
        HVACMode.HEAT,
        HVACMode.COOL,
        HVACMode.HEAT_COOL,
        HVACMode.FAN_ONLY,
    ]
    _attr_supported_features = (
        ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
        | ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.FAN_MODE
    )
    _attr_fan_modes = [FAN_AUTO, FAN_LOW, FAN_MEDIUM, FAN_HIGH]
    _attr_translation_key = "air_conditioner"

    def __init__(self, coordinator, initial_state, unique_id) -> None:
        super().__init__(coordinator, unique_id)

        self.ac_serial = unique_id
        self._attr_unique_id = unique_id

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, unique_id)},
            name=initial_state._state["NV_SystemSettings"]["SystemName"],
            manufacturer="Actron Air",
            model=initial_state._state["AirconSystem"]["MasterWCModel"],
            serial_number=initial_state._state["AirconSystem"]["MasterSerial"],
            sw_version=initial_state._state["AirconSystem"]["MasterWCFirmwareVersion"],
        )

        self._update_internal_state(initial_state)

    @callback
    def _handle_coordinator_update(self) -> None:
        state = self.coordinator.data[self.unique_id]

        self._update_internal_state(state)

        return super()._handle_coordinator_update()

    def _update_internal_state(self, state: ActronAdvanceState) -> None:
        _LOGGER.debug("Updating state for %s: %s", self.unique_id, state)

        # data
        is_on = state._state["UserAirconSettings"]["isOn"]
        mode = state._state["UserAirconSettings"]["Mode"]
        fan_mode = state._state["UserAirconSettings"]["FanMode"]
        continuous_fan = state._state["UserAirconSettings"]["FanMode"].endswith("+CONT")
        fan_mode = fan_mode.replace("+CONT", "")
        defrost = state._state["LiveAircon"]["Defrost"]
        compressor_mode = state._state["LiveAircon"]["CompressorMode"]

        def _hvac_mode(mode: str, is_on: bool) -> HVACMode:
            """Convert Actron mode to Home Assistant HVAC mode."""
            if not is_on:
                return HVACMode.OFF
            return HVAC_MODE_ACTRON_TO_HA[mode]

        def _hvac_action(
            mode: str,
            compressor_mode: str,
            continuous_fan: bool,
            is_on: bool,
            defrost: bool,
        ) -> HVACAction:
            """Convert Actron mode to Home Assistant HVAC action."""
            if not is_on:
                return HVACAction.OFF

            if defrost:
                return HVACAction.DEFROSTING

            if compressor_mode in HVAC_ACTION_ACTRON_TO_HA:
                return HVAC_ACTION_ACTRON_TO_HA[compressor_mode]

            if mode == "FAN" or continuous_fan:
                return HVACAction.FAN

            # Default to idle if no specific action is found
            return HVACAction.IDLE

        def _fan_mode(fan_mode: str) -> str:
            """Convert Actron fan mode to Home Assistant fan mode."""
            return FAN_MODE_ACTRON_TO_HA[fan_mode]

        def _current_temperature(state: ActronAdvanceState) -> float:
            """Get the current temperature from the state."""
            return state._state["MasterInfo"]["LiveTemp_oC"]

        def _current_humidity(state: ActronAdvanceState) -> float:
            """Get the current humidity from the state."""
            return state._state["MasterInfo"]["LiveHumidity_pc"]

        def _target_temperature(state: ActronAdvanceState, mode: str) -> float:
            """Get the target temperature from the state."""
            if mode == "HEAT":
                return state._state["UserAirconSettings"]["TemperatureSetpoint_Heat_oC"]
            elif mode == "COOL":
                return state._state["UserAirconSettings"]["TemperatureSetpoint_Cool_oC"]
            return None

        def _min_temp(state: ActronAdvanceState, mode: str) -> float:
            """Get the minimum temperature from the state."""
            if mode == "HEAT":
                return state._state["NV_Limits"]["UserSetpoint_oC"]["setHeat_Min"]
            elif mode == "COOL":
                return state._state["NV_Limits"]["UserSetpoint_oC"]["setCool_Min"]
            return None

        def _max_temp(state: ActronAdvanceState, mode: str) -> float:
            """Get the minimum temperature from the state."""
            if mode == "HEAT":
                return state._state["NV_Limits"]["UserSetpoint_oC"]["setHeat_Max"]
            elif mode == "COOL":
                return state._state["NV_Limits"]["UserSetpoint_oC"]["setCool_Max"]
            return None

        self._attr_hvac_mode = _hvac_mode(mode, is_on)
        self._attr_hvac_action = _hvac_action(
            mode, compressor_mode, continuous_fan, is_on, defrost
        )
        self._attr_fan_mode = _fan_mode(fan_mode)
        self._attr_current_temperature = _current_temperature(state)
        self._attr_current_humidity = _current_humidity(state)
        self._attr_target_temperature = _target_temperature(state, mode)
        self._attr_min_temp = _min_temp(state, mode)
        self._attr_max_temp = _max_temp(state, mode)

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        await self.coordinator.actron_api_client.set_system_mode(
            serial=self.unique_id,
            mode=HVAC_MODE_HA_TO_ACTRON[hvac_mode],
            is_on=hvac_mode != HVACMode.OFF,
        )

        # pre-emptively update local values given actron events can be slow
        self._attr_hvac_mode = hvac_mode
        # update hvac_action if we're confident
        if hvac_mode == HVACMode.OFF:
            self._attr_hvac_action = HVACAction.OFF
        # write the state back now we've pre-emptively updated it for responsiveness
        self.async_write_ha_state()

        # tell the coordinator to refresh data
        await self.coordinator.async_request_refresh()

    async def async_turn_on(self):
        """Turn the entity on."""
        await self.coordinator.actron_api_client.set_system_mode(
            serial=self.unique_id,
            is_on=True,
        )

        # pre-emptively update local values given actron events can be slow
        mode = self.coordinator.data[self.ac_serial]._state["UserAirconSettings"][
            "Mode"
        ]
        self._attr_hvac_mode = HVAC_MODE_ACTRON_TO_HA[mode]
        # write the state back now we've pre-emptively updated it for responsiveness
        self.async_write_ha_state()

        # tell the coordinator to refresh data
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self):
        """Turn the entity off."""
        await self.coordinator.actron_api_client.set_system_mode(
            serial=self.unique_id,
            is_on=False,
        )

        # pre-emptively update local values given actron events can be slow
        self._attr_hvac_mode = HVACMode.OFF
        self._attr_hvac_action = HVACAction.OFF
        # write the state back now we've pre-emptively updated it for responsiveness
        self.async_write_ha_state()

        # tell the coordinator to refresh data
        await self.coordinator.async_request_refresh()

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set new target fan mode."""
        # for continuous mode we want to use whatever the current setting is
        continuous = self.coordinator.data[self.ac_serial]._state["UserAirconSettings"]["FanMode"].endswith(
            "+CONT"
        )
        await self.coordinator.actron_api_client.set_fan_mode(
            serial=self.unique_id,
            mode=FAN_MODE_HA_TO_ACTRON[fan_mode],
            continuous=continuous,
        )

        # pre-emptively update local values given actron events can be slow
        self._attr_fan_mode = fan_mode
        # write the state back now we've pre-emptively updated it for responsiveness
        self.async_write_ha_state()

        # tell the coordinator to refresh data
        await self.coordinator.async_request_refresh()

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        temperature = kwargs[ATTR_TEMPERATURE]
        await self.coordinator.actron_api_client.set_temperature_setpoint(
            serial=self.ac_serial,
            cool=temperature,
            heat=temperature,
            zone_number=None,  # None means it's for the whole system
        )

        # pre-emptively update local values given actron events can be slow
        self._attr_target_temperature = temperature
        # write the state back now we've pre-emptively updated it for responsiveness
        self.async_write_ha_state()

        # tell the coordinator to refresh data
        await self.coordinator.async_request_refresh()


class ActronAirNimbusZone(ActronAirNimbusClimateEntity):
    """Representation of an Actron Air Nimbus zone."""

    _attr_supported_features = (
        ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
        | ClimateEntityFeature.TARGET_TEMPERATURE
    )
    _attr_translation_key = "zone"

    def __init__(self, coordinator, initial_state, ac_serial, zone_id) -> None:
        super().__init__(coordinator, zone_id)

        self._attr_unique_id = f"{ac_serial}_zone_{zone_id}"
        self.ac_serial = ac_serial
        self.zone_id = zone_id

        peripherals = [
            peripheral
            for peripheral in initial_state._state["AirconSystem"]["Peripherals"]
            if peripheral["DeviceType"] == "Zone Sensor"
        ]
        peripherals.sort(key=lambda x: x["ZoneAssignment"][0])

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self.unique_id)},
            via_device=(DOMAIN, ac_serial),
            name=f"{initial_state.zones[zone_id]['NV_Title']} zone",
            manufacturer="Actron Air",
            model=peripherals[zone_id]["DeviceType"],
            serial_number=peripherals[zone_id]["SerialNumber"],
            sw_version=peripherals[zone_id]["Firmware"]["InstalledVersion"]["NRF52"],
        )

        self._update_internal_state(initial_state)

    @callback
    def _handle_coordinator_update(self) -> None:
        state = self.coordinator.data[self.ac_serial]

        self._update_internal_state(state)

        return super()._handle_coordinator_update()

    def _update_internal_state(self, state: ActronAdvanceState) -> None:
        _LOGGER.debug(
            "Updating state for %s - zone %s: %s", self.unique_id, self.zone_id, state
        )

        # data
        is_on = state._state["UserAirconSettings"]["isOn"]
        mode = state._state["UserAirconSettings"]["Mode"]
        fan_mode = state._state["UserAirconSettings"]["FanMode"]
        continuous_fan = state._state["UserAirconSettings"]["FanMode"].endswith("+CONT")
        fan_mode = fan_mode.replace("+CONT", "")
        defrost = state._state["LiveAircon"]["Defrost"]
        compressor_mode = state._state["LiveAircon"]["CompressorMode"]
        zone_enabled = state._state["UserAirconSettings"]["EnabledZones"][self.zone_id]
        zone_damper_open = state.zones[self.zone_id]["ZonePosition"] != 0

        def _hvac_modes(mode: str) -> list[HVACMode]:
            return [
                HVACMode.OFF,
                HVAC_MODE_ACTRON_TO_HA[mode],
            ]

        def _hvac_mode(mode: str, zone_enabled: bool) -> HVACMode:
            """Convert Actron mode to Home Assistant HVAC mode."""
            if not zone_enabled:
                return HVACMode.OFF
            return HVAC_MODE_ACTRON_TO_HA[mode]

        def _hvac_action(
            mode: str,
            compressor_mode: str,
            continuous_fan: bool,
            is_on: bool,
            defrost: bool,
            zone_enabled: bool,
            zone_damper_open: bool,
        ) -> HVACAction:
            """Convert Actron mode to Home Assistant HVAC action."""
            if not is_on or not zone_enabled:
                return HVACAction.OFF

            # if the system is on and the zone is enabled, but the damper is
            # closed then we're idle
            if not zone_damper_open:
                return HVACAction.IDLE

            # if we're operating but the system is in defrost then this zone
            # is also in defrost
            if defrost:
                return HVACAction.DEFROSTING

            if compressor_mode in HVAC_ACTION_ACTRON_TO_HA:
                return HVAC_ACTION_ACTRON_TO_HA[compressor_mode]

            if mode == "FAN" or continuous_fan:
                return HVACAction.FAN

            # Default to idle if no specific action is found
            return HVACAction.IDLE

        def _current_temperature(state: ActronAdvanceState) -> float:
            """Get the current temperature from the state."""
            return state.zones[self.zone_id]["LiveTemp_oC"]

        def _current_humidity(state: ActronAdvanceState) -> float:
            """Get the current humidity from the state."""
            return state.zones[self.zone_id]["LiveHumidity_pc"]

        def _target_temperature(state: ActronAdvanceState, mode: str) -> float:
            """Get the target temperature from the state."""
            if mode == "HEAT":
                return state.zones[self.zone_id]["TemperatureSetpoint_Heat_oC"]
            elif mode == "COOL":
                return state.zones[self.zone_id]["TemperatureSetpoint_Cool_oC"]
            return None

        def _min_temp(state: ActronAdvanceState, mode: str) -> float:
            """Get the minimum temperature from the state."""
            if mode == "HEAT":
                return (
                    state._state["UserAirconSettings"]["TemperatureSetpoint_Heat_oC"]
                    - state._state["UserAirconSettings"][
                        "ZoneTemperatureSetpointVariance_oC"
                    ]
                )
            elif mode == "COOL":
                return (
                    state._state["UserAirconSettings"]["TemperatureSetpoint_Cool_oC"]
                    - state._state["UserAirconSettings"][
                        "ZoneTemperatureSetpointVariance_oC"
                    ]
                )
            return None

        def _max_temp(state: ActronAdvanceState, mode: str) -> float:
            """Get the maximum temperature from the state."""
            if mode == "HEAT":
                return (
                    state._state["UserAirconSettings"]["TemperatureSetpoint_Heat_oC"]
                    + state._state["UserAirconSettings"][
                        "ZoneTemperatureSetpointVariance_oC"
                    ]
                )
            elif mode == "COOL":
                return (
                    state._state["UserAirconSettings"]["TemperatureSetpoint_Cool_oC"]
                    + state._state["UserAirconSettings"][
                        "ZoneTemperatureSetpointVariance_oC"
                    ]
                )
            return None

        self._attr_hvac_mode = _hvac_mode(mode, zone_enabled)
        self._attr_hvac_action = _hvac_action(
            mode, compressor_mode, continuous_fan, is_on, defrost, zone_enabled,
            zone_damper_open
        )
        self._attr_current_temperature = _current_temperature(state)
        self._attr_current_humidity = _current_humidity(state)
        self._attr_target_temperature = _target_temperature(state, mode)
        self._attr_min_temp = _min_temp(state, mode)
        self._attr_max_temp = _max_temp(state, mode)

        # can only select either the mode that the parent is in, or off
        self._attr_hvac_modes = _hvac_modes(mode)

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        enabled_zones = self.coordinator.data[self.ac_serial]._state[
            "UserAirconSettings"
        ]["EnabledZones"]

        enabled_zones[self.zone_id] = hvac_mode != HVACMode.OFF

        await self.coordinator.actron_api_client.set_enabled_zones(
            serial=self.ac_serial,
            enabled_zones=enabled_zones,
        )

        # pre-emptively update local values given actron events can be slow
        self._attr_hvac_mode = hvac_mode
        # update hvac_action if we're confident
        if hvac_mode == HVACMode.OFF:
            self._attr_hvac_action = HVACAction.OFF
        # write the state back now we've pre-emptively updated it for responsiveness
        self.async_write_ha_state()

        # tell the coordinator to refresh data
        await self.coordinator.async_request_refresh()

    async def async_turn_on(self):
        """Turn the entity on."""
        enabled_zones = self.coordinator.data[self.ac_serial]._state[
            "UserAirconSettings"
        ]["EnabledZones"]
        enabled_zones[self.zone_id] = True
        await self.coordinator.actron_api_client.set_enabled_zones(
            serial=self.ac_serial,
            enabled_zones=enabled_zones,
        )

        # pre-emptively update local values given actron events can be slow
        mode = self.coordinator.data[self.ac_serial]._state["UserAirconSettings"][
            "Mode"
        ]
        self._attr_hvac_mode = HVAC_MODE_ACTRON_TO_HA[mode]
        # write the state back now we've pre-emptively updated it for responsiveness
        self.async_write_ha_state()

        # tell the coordinator to refresh data
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self):
        """Turn the entity off."""
        enabled_zones = self.coordinator.data[self.ac_serial]._state[
            "UserAirconSettings"
        ]["EnabledZones"]
        enabled_zones[self.zone_id] = False
        await self.coordinator.actron_api_client.set_enabled_zones(
            serial=self.ac_serial,
            enabled_zones=enabled_zones,
        )

        # pre-emptively update local values given actron events can be slow
        self._attr_hvac_mode = HVACMode.OFF
        self._attr_hvac_action = HVACAction.OFF
        # write the state back now we've pre-emptively updated it for responsiveness
        self.async_write_ha_state()

        # tell the coordinator to refresh data
        await self.coordinator.async_request_refresh()

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        temperature = kwargs[ATTR_TEMPERATURE]
        await self.coordinator.actron_api_client.set_temperature_setpoint(
            serial=self.ac_serial,
            cool=temperature,
            heat=temperature,
            zone_number=self.zone_id,
        )

        # pre-emptively update local values given actron events can be slow
        self._attr_target_temperature = temperature
        # TODO: should also update min/max temps too
        # write the state back now we've pre-emptively updated it for responsiveness
        self.async_write_ha_state()

        # tell the coordinator to refresh data
        await self.coordinator.async_request_refresh()
