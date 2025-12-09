import logging
from homeassistant.core import HomeAssistant
from .shadow_core import Shadow, ShadowConfig

_LOGGER = logging.getLogger(__name__)

DOMAIN = "shadow"

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Shadow integration."""

    async def handle_generate_svg(call):
        # Creează config din setările HA
        latitude = hass.config.latitude
        longitude = hass.config.longitude
        altitude = hass.config.elevation
        timezone = str(hass.config.time_zone)
        output_path = hass.config.path("www/shadow.svg")

        conf = ShadowConfig(
            latitude=latitude,
            longitude=longitude,
            altitude=altitude,
            timezone=timezone,
            town="Shadow",
            output_path=output_path
        )
        shadow = Shadow(conf)
        await shadow.async_generate_svg(hass)
        _LOGGER.info("Shadow SVG regenerated via service call")

    # Înregistrează serviciul
    hass.services.async_register(DOMAIN, "generate_svg", handle_generate_svg)

    return True
