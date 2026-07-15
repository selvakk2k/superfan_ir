import json
import logging
import os
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["fan"]

def load_codes(filepath: str) -> dict:
    with open(filepath, "r") as f:
        return json.load(f).get("data", {})

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Superfan IR from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    if "codes" not in hass.data[DOMAIN]:
        codes_file = os.path.join(os.path.dirname(__file__), "codes.json")
        try:
            hass.data[DOMAIN]["codes"] = await hass.async_add_executor_job(
                load_codes, codes_file
            )
        except Exception as e:
            _LOGGER.error("Failed to load codes.json: %s", e)
            return False

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)