import pytest
from unittest.mock import MagicMock
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from custom_components.superfan_ir.binary_sensor import SuperfanIRBlasterAvailableBinarySensor
from custom_components.superfan_ir.sensor import SuperfanLastControlledViaSensor
from custom_components.superfan_ir.const import MODEL_ATOMBERG, DOMAIN
from custom_components.superfan_ir import SuperfanEntryData


@pytest.fixture
def mock_entry():
    entry = MagicMock()
    entry.entry_id = "test_entry_id"
    entry.title = "Living Room Fan"
    entry.data = {"name": "Living Room Fan", "fan_model": MODEL_ATOMBERG, "emitter_entity_id": "infrared.blaster"}
    entry.options = {}
    return entry


@pytest.mark.asyncio
async def test_ir_blaster_available_binary_sensor(mock_entry):
    sensor = SuperfanIRBlasterAvailableBinarySensor(
        entry=mock_entry,
        fan_model=MODEL_ATOMBERG,
        emitter_id="infrared.blaster",
    )
    sensor.hass = MagicMock()
    
    # Blaster state is online
    blaster_state = MagicMock(state="idle")
    sensor.hass.states.get.return_value = blaster_state
    assert sensor.is_on is True

    # Blaster state is unavailable
    blaster_state.state = "unavailable"
    assert sensor.is_on is False

    # Blaster is ESPHome raw string (no dot)
    sensor._emitter_id = "ir_blaster"
    assert sensor.is_on is True


@pytest.mark.asyncio
async def test_last_controlled_via_sensor(mock_entry):
    sensor = SuperfanLastControlledViaSensor(
        entry=mock_entry,
        fan_model=MODEL_ATOMBERG,
    )
    sensor.hass = MagicMock()
    entry_data = SuperfanEntryData(mock_entry)
    sensor.hass.data = {DOMAIN: {mock_entry.entry_id: entry_data}}

    assert sensor.native_value == "Home Assistant"
    assert sensor.icon == "mdi:home-assistant"

    # Change to Physical IR Remote
    entry_data.set_last_controlled_via("Physical IR Remote")
    assert sensor.native_value == "Physical IR Remote"
    assert sensor.icon == "mdi:remote"

    # Change to Mains Switch
    entry_data.set_last_controlled_via("Mains Switch")
    assert sensor.native_value == "Mains Switch"
    assert sensor.icon == "mdi:toggle-switch"
