"""Sensor platform for Indian BLDC Fan integration."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    CONF_FAN_MODEL,
    DOMAIN,
    MODEL_ATOMBERG,
    MODEL_ACTIVA,
    MODEL_ORIENT,
    MODEL_GOLDMEDAL,
    MODEL_T10,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor entities."""
    fan_model = entry.options.get(
        CONF_FAN_MODEL, entry.data.get(CONF_FAN_MODEL, MODEL_ATOMBERG)
    )

    async_add_entities([
        SuperfanLastControlledViaSensor(
            entry=entry,
            fan_model=fan_model,
        )
    ])


class SuperfanLastControlledViaSensor(SensorEntity, RestoreEntity):
    """Diagnostic sensor reporting the last transport or trigger source that changed the fan."""

    _attr_has_entity_name = True
    _attr_translation_key = "last_controlled_via"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        entry: ConfigEntry,
        fan_model: str,
    ) -> None:
        """Initialize sensor."""
        self._entry = entry
        self._model = fan_model
        self._attr_unique_id = f"{entry.entry_id}_last_controlled_via"
        self._state_val = "Home Assistant"

        if self._model == MODEL_ATOMBERG:
            brand_name = "Atomberg"
        elif self._model == MODEL_ACTIVA:
            brand_name = "Activa Appliances"
        elif self._model == MODEL_ORIENT:
            brand_name = "Orient Electric"
        elif self._model == MODEL_GOLDMEDAL:
            brand_name = "Goldmedal Electricals"
        else:
            brand_name = "Versa Drives (Superfan)"

        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": brand_name,
            "model": fan_model,
        }

    @property
    def native_value(self) -> str:
        """Return current state."""
        entry_data = self.hass.data.get(DOMAIN, {}).get(self._entry.entry_id)
        if entry_data and hasattr(entry_data, "last_controlled_via"):
            return entry_data.last_controlled_via
        return self._state_val

    @property
    def icon(self) -> str:
        """Return dynamic icon."""
        val = self.native_value
        if val == "Physical IR Remote":
            return "mdi:remote"
        if val == "Mains Switch":
            return "mdi:toggle-switch"
        return "mdi:home-assistant"

    async def async_added_to_hass(self) -> None:
        """Restore state and attach listener."""
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state and last_state.state not in ("unavailable", "unknown"):
            self._state_val = last_state.state

        entry_data = self.hass.data.get(DOMAIN, {}).get(self._entry.entry_id)
        if entry_data and hasattr(entry_data, "add_listener"):
            self.async_on_remove(entry_data.add_listener(self._handle_update))

    @callback
    def _handle_update(self) -> None:
        """Handle runtime data update."""
        self.async_write_ha_state()
