from __future__ import annotations

import logging
from typing import Callable
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["fan", "sensor", "binary_sensor"]


class SuperfanEntryData:
    """Shared runtime data for a fan config entry."""

    def __init__(self, entry: ConfigEntry) -> None:
        self.entry = entry
        self.last_controlled_via: str = "IR Blaster"
        self.listeners: list[Callable[[], None]] = []

    def set_last_controlled_via(self, source: str) -> None:
        """Update last controlled source and notify listeners."""
        if self.last_controlled_via != source:
            self.last_controlled_via = source
            for listener in list(self.listeners):
                try:
                    listener()
                except Exception as err:
                    _LOGGER.debug("Error notifying listener: %s", err)

    def add_listener(self, listener: Callable[[], None]) -> Callable[[], None]:
        """Register a state listener."""
        self.listeners.append(listener)
        return lambda: self.listeners.remove(listener) if listener in self.listeners else None


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Superfan IR from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = SuperfanEntryData(entry)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry on options update."""
    await hass.config_entries.async_reload(entry.entry_id)
