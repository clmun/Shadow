from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.event import async_track_time_interval

from .const import (
    DOMAIN,
    DEFAULT_NAME,
    DEFAULT_UPDATE_INTERVAL_MIN,
    DEFAULT_OUTPUT_PATH,
    CONF_TOWN,
    CONF_OUTPUT_PATH,
    CONF_UPDATE_INTERVAL,
)
from .shadow_core import Shadow, ShadowConfig

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities,
    discovery_info=None
):
    name = config.get(CONF_NAME, DEFAULT_NAME)
    latitude = hass.config.latitude
    longitude = hass.config.longitude
    altitude = hass.config.elevation or 0
    timezone = hass.config.time_zone
    town = config.get(CONF_TOWN, "Home")
    output_path = config.get(CONF_OUTPUT_PATH, DEFAULT_OUTPUT_PATH)
    update_interval_min = int(config.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL_MIN))

    shadow_conf = ShadowConfig(
        latitude=latitude,
        longitude=longitude,
        altitude=altitude,
        timezone=timezone,
        town=town,
        output_path=output_path,
    )

    entity = ShadowSensor(name, shadow_conf)
    async_add_entities([entity])

    async def _scheduled_update(now):
        await entity.async_update_svg()

    async_track_time_interval(hass, _scheduled_update, timedelta(minutes=update_interval_min))


class ShadowSensor(SensorEntity):
    def __init__(self, name: str, conf: ShadowConfig):
        self._attr_name = name
        self._conf = conf
        self._shadow = Shadow(conf)
        self._attr_unique_id = f"{DOMAIN}_{name.lower().replace(' ', '_')}"
        self._state = None
        self._attrs = {}
        self._available = True

    @property
    def available(self) -> bool:
        return self._available

    @property
    def state(self):
        return self._state

    @property
    def extra_state_attributes(self):
        return self._attrs

    async def async_update(self):
        try:
            self._shadow.refresh()
            self._state = round(self._shadow.elevation, 2)
            self._attrs = {
                "sun_azimuth": round(self._shadow.sun_azimuth, 2),
                "sun_elevation": round(self._shadow.sun_elevation, 2),
                "sunrise_azimuth": round(self._shadow.sunrise_azimuth, 2),
                "sunset_azimuth": round(self._shadow.sunset_azimuth, 2),
                "moon_azimuth": round(self._shadow.moon_azimuth, 2),
                "moon_elevation": round(self._shadow.moon_elevation, 2),
                "svg_path": self._conf.output_path
            }
            self._available = True
        except Exception as e:
            _LOGGER.exception("Shadow update failed: %s", e)
            self._available = False

    async def async_update_svg(self):
        try:
            self._shadow.refresh()
            self._shadow.generate_svg()
            await self.async_update_ha_state(True)
        except Exception as e:
            _LOGGER.exception("Shadow SVG generation failed: %s", e)
            self._available = False

    async def async_call_action(self, action: str, data: dict) -> None:
        """Handle actions defined in manifest.json."""
        if action == "generate_svg":
            await self.async_update_svg()
