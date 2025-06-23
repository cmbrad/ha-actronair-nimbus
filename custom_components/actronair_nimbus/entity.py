from homeassistant.helpers.update_coordinator import CoordinatorEntity


class ActronAirNimbusEntity(CoordinatorEntity):
    """Base class for Actron Air Nimbus entities."""

    _attr_has_entity_name = True
