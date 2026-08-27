from __future__ import annotations

from typing import Any
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.components.diagnostics import async_redact_data

from .const import (
    CONF_FAN_MODEL,
    MODEL_ACTIVA,
    MODEL_ATOMBERG,
    MODEL_GOLDMEDAL,
    MODEL_ORIENT,
    MODEL_T10,
)
from .ir import (
    ACTIVA_COMMAND_BYTES,
    ATOMBERG_COMMAND_BYTES,
    GOLDMEDAL_COMMAND_BYTES,
    ORIENT_COMMAND_BYTES,
    SUPERFAN_COMMAND_BYTES,
    SuperfanNEC,
)

TO_REDACT = {"emitter_entity_id", "receiver_entity_id", "unique_id"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    model = entry.options.get(CONF_FAN_MODEL, entry.data.get(CONF_FAN_MODEL, MODEL_ATOMBERG))
    if model == MODEL_ATOMBERG:
        commands = list(ATOMBERG_COMMAND_BYTES.keys())
    elif model == MODEL_ACTIVA:
        commands = list(ACTIVA_COMMAND_BYTES.keys())
    elif model == MODEL_ORIENT:
        commands = list(ORIENT_COMMAND_BYTES.keys())
    elif model == MODEL_GOLDMEDAL:
        commands = list(GOLDMEDAL_COMMAND_BYTES.keys())
    else:
        commands = list(SUPERFAN_COMMAND_BYTES.keys())

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
