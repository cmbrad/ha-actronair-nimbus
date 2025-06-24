from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.components.switch import SwitchEntity
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
        entities.append(QuietModeEnabledSwitch(coordinator, state, unique_id))
        entities.append(TurboModeEnabledSwitch(coordinator, state, unique_id))
        entities.append(ContinuousFanEnabledSwitch(coordinator, state, unique_id))
        entities.append(AwayModeEnabledSwitch(coordinator, state, unique_id))

    async_add_entities(entities)


class QuietModeEnabledSwitch(ActronAirNimbusEntity, SwitchEntity):
    """Representation of a Quiet Mode switch."""

    _attr_translation_key = "quiet_mode_enabled"

    def __init__(self, coordinator, initial_state, ac_serial: str) -> None:
        super().__init__(coordinator, ac_serial)
        self.ac_serial = ac_serial

        self._attr_unique_id = f"{ac_serial}_quiet_mode_enabled"

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
        self._attr_is_on = state._state["UserAirconSettings"]["QuietModeEnabled"]

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.actron_api_client.set_settings(
            serial=self.ac_serial,
            settings={"UserAirconSettings.QuietModeEnabled": True},
        )

        # pre-emptively update local values given actron events can be slow
        self._attr_is_on = True
        # write the state back now we've pre-emptively updated it for responsiveness
        self.async_write_ha_state()

        # tell the coordinator to refresh data
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.actron_api_client.set_settings(
            serial=self.ac_serial,
            settings={"UserAirconSettings.QuietModeEnabled": False},
        )

        # pre-emptively update local values given actron events can be slow
        self._attr_is_on = False
        # write the state back now we've pre-emptively updated it for responsiveness
        self.async_write_ha_state()

        # tell the coordinator to refresh data
        await self.coordinator.async_request_refresh()


class TurboModeEnabledSwitch(ActronAirNimbusEntity, SwitchEntity):
    """Representation of a Turbo Mode switch."""

    _attr_translation_key = "turbo_mode_enabled"

    def __init__(self, coordinator, initial_state, ac_serial: str) -> None:
        super().__init__(coordinator, ac_serial)
        self.ac_serial = ac_serial

        self._attr_unique_id = f"{ac_serial}_turbo_mode_enabled"

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
        self._attr_is_on = state._state["UserAirconSettings"]["TurboMode"]["Enabled"]

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.actron_api_client.set_settings(
            serial=self.ac_serial,
            settings={"UserAirconSettings.TurboMode.Enabled": True},
        )

        # pre-emptively update local values given actron events can be slow
        self._attr_is_on = True
        # write the state back now we've pre-emptively updated it for responsiveness
        self.async_write_ha_state()

        # tell the coordinator to refresh data
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.actron_api_client.set_settings(
            serial=self.ac_serial,
            settings={"UserAirconSettings.TurboMode.Enabled": False},
        )

        # pre-emptively update local values given actron events can be slow
        self._attr_is_on = False
        # write the state back now we've pre-emptively updated it for responsiveness
        self.async_write_ha_state()

        # tell the coordinator to refresh data
        await self.coordinator.async_request_refresh()


class ContinuousFanEnabledSwitch(ActronAirNimbusEntity, SwitchEntity):
    """Representation of a Continuous Fan switch."""

    _attr_translation_key = "continuous_fan_enabled"

    def __init__(self, coordinator, initial_state, ac_serial: str) -> None:
        super().__init__(coordinator, ac_serial)
        self.ac_serial = ac_serial

        self._attr_unique_id = f"{ac_serial}_continuous_fan_enabled"

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
        self._attr_is_on = state._state["UserAirconSettings"]["FanMode"].endswith(
            "+CONT"
        )

    async def async_turn_on(self, **kwargs) -> None:
        fan_mode = (
            self.coordinator.data[self.ac_serial]
            ._state["UserAirconSettings"]["FanMode"]
            .replace("+CONT", "")
        )
        await self.coordinator.actron_api_client.set_settings(
            serial=self.ac_serial,
            settings={"UserAirconSettings.FanMode": f"{fan_mode}+CONT"},
        )

        # pre-emptively update local values given actron events can be slow
        self._attr_is_on = True
        # write the state back now we've pre-emptively updated it for responsiveness
        self.async_write_ha_state()

        # tell the coordinator to refresh data
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        fan_mode = (
            self.coordinator.data[self.ac_serial]
            ._state["UserAirconSettings"]["FanMode"]
            .replace("+CONT", "")
        )
        await self.coordinator.actron_api_client.set_settings(
            serial=self.ac_serial,
            settings={"UserAirconSettings.FanMode": fan_mode},
        )

        # pre-emptively update local values given actron events can be slow
        self._attr_is_on = False
        # write the state back now we've pre-emptively updated it for responsiveness
        self.async_write_ha_state()

        # tell the coordinator to refresh data
        await self.coordinator.async_request_refresh()


class AwayModeEnabledSwitch(ActronAirNimbusEntity, SwitchEntity):
    """Representation of an Away Mode switch."""

    _attr_translation_key = "away_mode_enabled"

    def __init__(self, coordinator, initial_state, ac_serial: str) -> None:
        super().__init__(coordinator, ac_serial)
        self.ac_serial = ac_serial

        self._attr_unique_id = f"{ac_serial}_away_mode_enabled"

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
        self._attr_is_on = state._state["UserAirconSettings"]["AwayMode"]

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.actron_api_client.set_settings(
            serial=self.ac_serial,
            settings={"UserAirconSettings.AwayMode": True},
        )

        # pre-emptively update local values given actron events can be slow
        self._attr_is_on = True
        # write the state back now we've pre-emptively updated it for responsiveness
        self.async_write_ha_state()

        # tell the coordinator to refresh data
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.actron_api_client.set_settings(
            serial=self.ac_serial,
            settings={"UserAirconSettings.AwayMode": False},
        )

        # pre-emptively update local values given actron events can be slow
        self._attr_is_on = False
        # write the state back now we've pre-emptively updated it for responsiveness
        self.async_write_ha_state()

        # tell the coordinator to refresh data
        await self.coordinator.async_request_refresh()
