from homeassistant.core import HomeAssistant
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

    @property
    def is_on(self) -> bool:
        return self.coordinator.data[self.ac_serial]._state["UserAirconSettings"][
            "QuietModeEnabled"
        ]

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.actron_api_client.set_settings(
            serial=self._system_serial,
            settings={"UserAirconSettings.QuietModeEnabled": True},
        )

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.actron_api_client.set_settings(
            serial=self._system_serial,
            settings={"UserAirconSettings.QuietModeEnabled": False},
        )


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

    @property
    def is_on(self) -> bool:
        return self.coordinator.data[self.ac_serial]._state["UserAirconSettings"][
            "TurboMode"
        ]["Enabled"]

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.actron_api_client.set_settings(
            serial=self._system_serial,
            settings={"UserAirconSettings.TurboMode.Enabled": True},
        )

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.actron_api_client.set_settings(
            serial=self._system_serial,
            settings={"UserAirconSettings.TurboMode.Enabled": False},
        )


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

    @property
    def is_on(self) -> bool:
        return (
            self.coordinator.data[self.ac_serial]
            ._state["UserAirconSettings"]["FanMode"]
            .endswith("+CONT")
        )

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.actron_api_client.set_settings(
            serial=self._system_serial,
            settings={"UserAirconSettings.FanMode": "Continuous"},
        )

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.actron_api_client.set_settings(
            serial=self._system_serial,
            settings={"UserAirconSettings.FanMode": "Auto"},
        )


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

    @property
    def is_on(self) -> bool:
        return self.coordinator.data[self.ac_serial]._state["UserAirconSettings"][
            "AwayMode"
        ]

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.actron_api_client.set_settings(
            serial=self._system_serial,
            settings={"UserAirconSettings.AwayMode": True},
        )

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.actron_api_client.set_settings(
            serial=self._system_serial,
            settings={"UserAirconSettings.AwayMode": False},
        )
