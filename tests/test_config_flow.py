import pytest
from unittest.mock import MagicMock
from custom_components.superfan_ir.config_flow import SuperfanConfigFlow, SuperfanOptionsFlow
from custom_components.superfan_ir.const import (
    CONF_EMITTER_ENTITY_ID,
    CONF_FAN_MODEL,
    CONF_IR_FORMAT,
    CONF_POWER_SWITCH,
    CONF_RECEIVER_ENTITY_ID,
    IR_FORMAT_AUTO,
    IR_FORMAT_PRONTO,
    MODEL_ATOMBERG,
    MODEL_T10,
)


@pytest.mark.asyncio
async def test_config_flow_user_and_emitter_steps():
    flow = SuperfanConfigFlow()
    flow.hass = MagicMock()

    # Step 1: User Step
    res1 = await flow.async_step_user({
        "name": "Balcony Fan",
        CONF_FAN_MODEL: MODEL_ATOMBERG,
        CONF_IR_FORMAT: IR_FORMAT_AUTO,
    })
    assert res1["type"] == "form"
    assert res1["step_id"] == "emitter"

    # Step 2: Emitter Step
    res2 = await flow.async_step_emitter({CONF_EMITTER_ENTITY_ID: "infrared.blaster_2"})
    assert res2["type"] == "create_entry"
    assert res2["title"] == "Balcony Fan"
    assert res2["data"][CONF_EMITTER_ENTITY_ID] == "infrared.blaster_2"
    assert res2["data"][CONF_FAN_MODEL] == MODEL_ATOMBERG


@pytest.mark.asyncio
async def test_options_flow():
    entry = MagicMock()
    entry.data = {
        "name": "Balcony Fan",
        CONF_FAN_MODEL: MODEL_T10,
        CONF_IR_FORMAT: IR_FORMAT_AUTO,
        CONF_EMITTER_ENTITY_ID: "infrared.blaster_2",
    }
    entry.options = {}

    flow = SuperfanOptionsFlow(entry)
    flow.hass = MagicMock()

    res = await flow.async_step_init({
        CONF_FAN_MODEL: MODEL_ATOMBERG,
        CONF_IR_FORMAT: IR_FORMAT_PRONTO,
        CONF_EMITTER_ENTITY_ID: "remote.broadlink_rm",
        CONF_RECEIVER_ENTITY_ID: "sensor.esphome_rx",
        CONF_POWER_SWITCH: "switch.smart_plug",
    })
    assert res["type"] == "create_entry"
    assert res["data"][CONF_FAN_MODEL] == MODEL_ATOMBERG
    assert res["data"][CONF_IR_FORMAT] == IR_FORMAT_PRONTO
    assert res["data"][CONF_EMITTER_ENTITY_ID] == "remote.broadlink_rm"
    assert res["data"][CONF_RECEIVER_ENTITY_ID] == "sensor.esphome_rx"
    assert res["data"][CONF_POWER_SWITCH] == "switch.smart_plug"
