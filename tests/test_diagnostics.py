import pytest
from unittest.mock import MagicMock
from custom_components.superfan_ir.diagnostics import async_get_config_entry_diagnostics


@pytest.mark.asyncio
async def test_diagnostics_structure():
    hass = MagicMock()
    entry = MagicMock()
    entry.entry_id = "test_entry_123"
    entry.title = "Living Room Superfan"
    entry.data = {"fan_model": "SuperfanT10", "emitter_entity_id": "infrared.blaster_1"}
    entry.options = {"power_switch": "switch.fan_plug", "receiver_entity_id": "sensor.ir_rx"}

    diag = await async_get_config_entry_diagnostics(hass, entry)
    assert diag["entry_id"] == "test_entry_123"
    assert diag["title"] == "Living Room Superfan"
    assert diag["protocol"] == "NEC_32BIT"
    assert diag["address"] == "0x00DF"
    assert "Power" in diag["supported_commands"]
    assert diag["data"]["emitter_entity_id"] == "**REDACTED**"
    assert diag["options"]["receiver_entity_id"] == "**REDACTED**"
