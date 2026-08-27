from __future__ import annotations

from typing import Any
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.components.diagnostics import async_redact_data

from .const import CONF_FAN_MODEL, MODEL_ATOMBERG, MODEL_T10
from .ir import ATOMBERG_COMMAND_BYTES, SUPERFAN_COMMAND_BYTES, SuperfanNEC

TO_REDACT = {"emitter_entity_id", "receiver_entity_id", "unique_id"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    model = entry.options.get(CONF_FAN_MODEL, entry.data.get(CONF_FAN_MODEL, MODEL_T10))
    commands = (
        list(ATOMBERG_COMMAND_BYTES.keys())
        if model == MODEL_ATOMBERG
        else list(SUPERFAN_COMMAND_BYTES.keys())
    )
    addr = f"0x{SuperfanNEC.get_address(model):04X}"

    return {
        "entry_id": entry.entry_id,
        "title": entry.title,
        "data": async_redact_data(dict(entry.data), TO_REDACT),
        "options": async_redact_data(dict(entry.options), TO_REDACT),
        "protocol": "NEC_32BIT",
        "model": model,
        "address": addr,
        "supported_commands": commands,
    }
