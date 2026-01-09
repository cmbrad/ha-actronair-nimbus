from homeassistant.core import HomeAssistant
from homeassistant.components.persistent_notification import async_create


def create_notification(hass: HomeAssistant, message: str, title: str):
    """Create a notification."""
    async_create(
        hass,
        message, 
        title=title
    )

