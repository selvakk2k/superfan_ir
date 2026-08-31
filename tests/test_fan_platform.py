import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from homeassistant.components.fan import FanEntityFeature
from homeassistant.core import Event
from custom_components.superfan_ir.fan import SuperfanEntity
from custom_components.superfan_ir.const import (
    MODEL_ATOMBERG,
    MODEL_T10,
    MODEL_T12_6,
    BACKEND_INFRARED,
    CONF_POWER_SWITCH,
    CONF_RECEIVER_ENTITY_ID,
)


@pytest.fixture
def mock_entry():
    entry = MagicMock()
    entry.entry_id = "superfan_entry_id"
    entry.title = "Master Bedroom Fan"
    entry.data = {
        "name": "Master Bedroom Fan",
        "fan_model": MODEL_T10,
        "backend": BACKEND_INFRARED,
        "emitter_entity_id": "infrared.living_blaster",
    }
    entry.options = {}
    return entry


@pytest.mark.asyncio
async def test_superfan_t10_state_memory_retention(mock_entry):
    fan = SuperfanEntity(
        entry=mock_entry,
        fan_model=MODEL_T10,
        backend=BACKEND_INFRARED,
        emitter_id="infrared.living_blaster",
    )
    fan.entity_id = "fan.master_bedroom_fan"
    fan.hass = MagicMock()
    fan.hass.services.async_call = AsyncMock()

    # 1. Turn on and set percentage to 80% (Speed 4)
    with patch.object(fan, "_send_ir_command", new_callable=AsyncMock), patch.object(fan, "async_write_ha_state"):
        await fan.async_set_percentage(80)
        assert fan.is_on is True
        assert fan.percentage == 80

    # 2. Turn off (percentage goes to 0, but _last_percentage stays 80)
    with patch.object(fan, "_send_ir_command", new_callable=AsyncMock), patch.object(fan, "async_write_ha_state"):
        await fan.async_turn_off()
        assert fan.is_on is False
        assert fan.percentage == 0
        assert fan._last_percentage == 80

    # 3. Turn on without args (restores 80% speed code "4" instead of resetting to default)
    with patch.object(fan, "_send_ir_command", new_callable=AsyncMock) as mock_send, patch.object(fan, "async_write_ha_state"):
        await fan.async_turn_on()
        assert fan.is_on is True
        assert fan.percentage == 80
        mock_send.assert_called_with("4")

    # 4. Turn on with active preset (restores preset mode IR command)
    with patch.object(fan, "_send_ir_command", new_callable=AsyncMock) as mock_send, patch.object(fan, "async_write_ha_state"):
        await fan.async_set_preset_mode("Breeze Mode")
        await fan.async_turn_off()
        await fan.async_turn_on()
        assert fan.is_on is True
        assert fan.preset_mode == "Breeze Mode"
        mock_send.assert_called_with("Breeze Mode")


@pytest.mark.asyncio
async def test_atomberg_fan_speeds_and_presets(mock_entry):
    mock_entry.title = "Living Room Atomberg Fan"
    fan = SuperfanEntity(
        entry=mock_entry,
        fan_model=MODEL_ATOMBERG,
        backend=BACKEND_INFRARED,
        emitter_id="infrared.living_blaster",
    )
    fan.entity_id = "fan.living_room_atomberg_fan"
    fan.hass = MagicMock()
    fan.hass.services.async_call = AsyncMock()

    assert fan.speed_count == 6
    assert "Sleep Mode" in fan.preset_modes
    assert "LED Light" in fan.preset_modes

    # Set speed to 100% (Boost)
    with patch.object(fan, "_send_ir_command", new_callable=AsyncMock) as mock_send, patch.object(fan, "async_write_ha_state"):
        await fan.async_set_percentage(100)
        assert fan.is_on is True
        assert fan.percentage == 100
        mock_send.assert_called_with("Boost")

    # Set preset to Sleep Mode
    with patch.object(fan, "_send_ir_command", new_callable=AsyncMock) as mock_send, patch.object(fan, "async_write_ha_state"):
        await fan.async_set_preset_mode("Sleep Mode")
        assert fan.is_on is True
        assert fan.preset_mode == "Sleep Mode"
        mock_send.assert_called_with("Sleep Mode")


@pytest.mark.asyncio
async def test_smart_switch_power_interlock(mock_entry):
    fan = SuperfanEntity(
        entry=mock_entry,
        fan_model=MODEL_T10,
        backend=BACKEND_INFRARED,
        emitter_id="infrared.living_blaster",
        power_switch="switch.fan_smart_plug",
    )
    fan.entity_id = "fan.master_bedroom_fan"
    fan.hass = MagicMock()
    fan.hass.services.async_call = AsyncMock()

    switch_state = MagicMock()
    switch_state.state = "off"
    fan.hass.states.get.return_value = switch_state

    # Turning on should turn on smart switch, sleep 1.5s boot delay, and send restored speed IR (3 for default 60%)
    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep, patch.object(fan, "_send_ir_command", new_callable=AsyncMock) as mock_send, patch.object(fan, "async_write_ha_state"):
        await fan.async_turn_on()
        fan.hass.services.async_call.assert_called_with(
            "switch", "turn_on", {"entity_id": "switch.fan_smart_plug"}, context=fan._context
        )
        mock_sleep.assert_called_with(1.5)
        mock_send.assert_called_with("3")

    # Turning off should turn off smart switch directly
    with patch.object(fan, "_send_ir_command", new_callable=AsyncMock) as mock_send, patch.object(fan, "async_write_ha_state"):
        await fan.async_turn_off()
        fan.hass.services.async_call.assert_called_with(
            "switch", "turn_off", {"entity_id": "switch.fan_smart_plug"}, context=fan._context
        )
        # Power IR should NOT be sent when power switch is present
        mock_send.assert_not_called()


@pytest.mark.asyncio
async def test_physical_remote_ir_receiver_sync_atomberg(mock_entry):
    fan = SuperfanEntity(
        entry=mock_entry,
        fan_model=MODEL_ATOMBERG,
        backend=BACKEND_INFRARED,
        emitter_id="infrared.living_blaster",
        receiver_id="sensor.esphome_ir_receiver",
    )
    fan.entity_id = "fan.living_room_atomberg_fan"
    fan.hass = MagicMock()
    fan.hass.services.async_call = AsyncMock()

    # Physical remote: Speed 3 (0xF300758A)
    event_data = {
        "new_state": MagicMock(state="0xF300758A")
    }
    event = Event("state_changed", data=event_data)

    with patch.object(fan, "async_write_ha_state") as mock_write:
        await fan._async_receiver_event(event)
        assert fan.is_on is True
        assert fan.percentage == 50  # Speed 3 for Atomberg
        mock_write.assert_called()

    # Physical remote: Boost button (0xF300708F)
    event_boost = Event("state_changed", data={"new_state": MagicMock(state="0xF300708F")})
    with patch.object(fan, "async_write_ha_state") as mock_write:
        await fan._async_receiver_event(event_boost)
        assert fan.is_on is True
        assert fan.percentage == 100  # Boost
        mock_write.assert_called()

    # Physical remote: Power toggle (0xF3006E91)
    event_power = Event("state_changed", data={"new_state": MagicMock(state="0xF3006E91")})
    with patch.object(fan, "async_write_ha_state") as mock_write:
        await fan._async_receiver_event(event_power)
        assert fan.is_on is False
        assert fan.percentage == 0
        mock_write.assert_called()


@pytest.mark.asyncio
async def test_send_ir_command_auto_detect_tuya(mock_entry):
    """Test that generic remote.* entities auto-detect to IR_FORMAT_TUYA."""
    from custom_components.superfan_ir.const import IR_FORMAT_AUTO
    fan = SuperfanEntity(
        entry=mock_entry,
        fan_model=MODEL_T10,
        emitter_id="remote.tuya_ir_blaster",
        ir_format=IR_FORMAT_AUTO,
    )
    fan.entity_id = "fan.test_fan"
    fan.hass = MagicMock()
    fan.hass.services.async_call = AsyncMock()

    await fan._send_ir_command("1")
    fan.hass.services.async_call.assert_called_once()
    domain, service, service_data = fan.hass.services.async_call.call_args[0]
    assert domain == "remote"
    assert service == "send_command"
    assert service_data["entity_id"] == "remote.tuya_ir_blaster"
    from custom_components.superfan_ir.ir import SuperfanNEC
    assert service_data["command"][0] == SuperfanNEC.get_tuya_base64("1", MODEL_T10)


@pytest.mark.asyncio
async def test_send_ir_command_auto_detect_broadlink(mock_entry):
    """Test that broadlink remote entities auto-detect to IR_FORMAT_BROADLINK."""
    from custom_components.superfan_ir.const import IR_FORMAT_AUTO
    fan = SuperfanEntity(
        entry=mock_entry,
        fan_model=MODEL_T10,
        emitter_id="remote.broadlink_rm4_pro",
        ir_format=IR_FORMAT_AUTO,
    )
    fan.entity_id = "fan.test_fan"
    fan.hass = MagicMock()
    fan.hass.services.async_call = AsyncMock()

    await fan._send_ir_command("1")
    fan.hass.services.async_call.assert_called_once()
    domain, service, service_data = fan.hass.services.async_call.call_args[0]
    assert domain == "remote"
    assert service == "send_command"
    assert service_data["entity_id"] == "remote.broadlink_rm4_pro"
    assert service_data["command"][0].startswith("b64:")


@pytest.mark.asyncio
async def test_send_ir_command_auto_detect_esphome(mock_entry):
    """Test that esphome emitters auto-detect to IR_FORMAT_RAW."""
    from custom_components.superfan_ir.const import IR_FORMAT_AUTO
    fan = SuperfanEntity(
        entry=mock_entry,
        fan_model=MODEL_T10,
        emitter_id="esphome.bedroom_fan_emitter",
        ir_format=IR_FORMAT_AUTO,
    )
    fan.entity_id = "fan.test_fan"
    fan.hass = MagicMock()
    fan.hass.services.async_call = AsyncMock()

    await fan._send_ir_command("1")
    fan.hass.services.async_call.assert_called_once()
    domain, service, service_data = fan.hass.services.async_call.call_args[0]
    assert domain == "esphome"
    assert service == "bedroom_fan_emitter_transmit_raw"
    assert "command" in service_data


@pytest.mark.asyncio
async def test_send_ir_command_missing_emitter_returns_false(mock_entry):
    """Test that missing or empty emitter_id returns False and does not crash or update state."""
    fan = SuperfanEntity(
        entry=mock_entry,
        fan_model=MODEL_T10,
        emitter_id="",
    )
    fan.entity_id = "fan.test_fan"
    fan.hass = MagicMock()

    result = await fan._send_ir_command("1")
    assert result is False

    await fan.async_set_percentage(80)
    assert fan.is_on is False
    assert fan.percentage == 0


@pytest.mark.asyncio
async def test_send_ir_command_failure_returns_false_and_preserves_state(mock_entry):
    """Test that synchronous transport failure returns False without raising and preserves entity state."""
    fan = SuperfanEntity(
        entry=mock_entry,
        fan_model=MODEL_T10,
        emitter_id="remote.tuya_ir_blaster",
    )
    fan.entity_id = "fan.test_fan"
    fan.hass = MagicMock()
    fan.hass.services.async_call = AsyncMock(side_effect=RuntimeError("Connection refused"))

    result = await fan._send_ir_command("1")
    assert result is False

    # Calling async_set_percentage when transport fails should return early without setting state to ON
    await fan.async_set_percentage(80)
    assert fan.is_on is False
    assert fan.percentage == 0
