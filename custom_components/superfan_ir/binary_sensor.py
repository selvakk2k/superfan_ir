"""Binary sensor platform for Indian BLDC Fan integration."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    CONF_EMITTER_ENTITY_ID,
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
    """Set up binary sensor entities."""
    emitter_id = entry.options.get(
        CONF_EMITTER_ENTITY_ID, entry.data.get(CONF_EMITTER_ENTITY_ID)
    )
    fan_model = entry.options.get(
        CONF_FAN_MODEL, entry.data.get(CONF_FAN_MODEL, MODEL_ATOMBERG)
    )

    async_add_entities([
        SuperfanIRBlasterAvailableBinarySensor(
            entry=entry,
            fan_model=fan_model,
            emitter_id=emitter_id,
        )
    ])


class SuperfanIRBlasterAvailableBinarySensor(BinarySensorEntity):
    """Binary sensor reporting connectivity/availability of the configured IR transmitter."""

    _attr_has_entity_name = True
    _attr_translation_key = "ir_blaster_available"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        entry: ConfigEntry,
        fan_model: str,
        emitter_id: str | None,
    ) -> None:
        """Initialize binary sensor."""
        self._entry = entry
        self._model = fan_model
        self._emitter_id = emitter_id
        self._attr_unique_id = f"{entry.entry_id}_ir_blaster_available"

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
    def is_on(self) -> bool:
        """Return true if the IR blaster is online and available."""
        if not self._emitter_id:
            return False
        # ESPHome text/service names don't map to HA states directly, so assume True if set
        if not ("." in self._emitter_id):
            return True
        st = self.hass.states.get(self._emitter_id)
        return st is not None and st.state not in ("unavailable", "unknown")

    async def async_added_to_hass(self) -> None:
        """Register state change listeners."""
        await super().async_added_to_hass()
        if self._emitter_id and "." in self._emitter_id:
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass, [self._emitter_id], self._async_emitter_changed
                )
            )

    @callback
    def _async_emitter_changed(self, event: Event) -> None:
        """Handle blaster state change."""
        self.async_write_ha_state()
