from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    # Platform-based (YAML) setup — sensor.py will handle entities
    _LOGGER.debug("Shadow integration setup (platform)")
    return True

async def async_setup_entry(hass: HomeAssistant, entry):
    # Not using config entries for now
    return True

async def async_unload_entry(hass: HomeAssistant, entry):
    return True
