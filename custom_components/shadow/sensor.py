import logging
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.typing import HomeAssistantType, ConfigType, DiscoveryInfoType
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, CONF_ELEVATION, CONF_NAME, CONF_TIME_ZONE
from .shadow_core import Shadow, ShadowConfig

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(hass: HomeAssistantType, config: ConfigType, async_add_entities, discovery_info: DiscoveryInfoType | None = None):
    """Set up the Shadow sensor platform."""
    name = config.get(CONF_NAME, "Shadow")
    latitude = config.get(CONF_LATITUDE, hass.config.latitude)
    longitude = config.get(CONF_LONGITUDE, hass.config.longitude)
    altitude = config.get(CONF_ELEVATION, hass.config.elevation)
    timezone = config.get(CONF_TIME_ZONE, str(hass.config.time_zone))
    output_path = hass.config.path("www/shadow.svg")

    conf = ShadowConfig(
        latitude=latitude,
        longitude=longitude,
        altitude=altitude,
        timezone=timezone,
        town=name,
        output_path=output_path
    )

    shadow = Shadow(conf)
    async_add_entities([ShadowSensor(hass, shadow)], True)

class ShadowSensor(Entity):
    """Representation of the Shadow sensor."""

    def __init__(self, hass: HomeAssistantType, shadow: Shadow):
        self._hass = hass
        self._shadow = shadow
        self._state = None

    @property
    def name(self):
        return self._shadow.conf.town

    @property
    def state(self):
        return self._state

    async def async_update(self):
        """Update sensor state and regenerate SVG."""
        self._shadow.refresh()
        self._state = f"Sun elev: {self._shadow.sun_elevation:.2f}, Moon elev: {self._shadow.moon_elevation:.2f}"
        await self._shadow.async_generate_svg(self._hass)
