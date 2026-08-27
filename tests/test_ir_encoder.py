import base64
from struct import unpack
import pytest

from custom_components.superfan_ir.ir import (
    SuperfanNEC,
    SUPERFAN_ADDRESS,
    ATOMBERG_ADDRESS,
    NEC_HDR_MARK,
    NEC_HDR_SPACE,
    NEC_BIT_MARK,
    NEC_ONE_SPACE,
    NEC_ZERO_SPACE,
)
from custom_components.superfan_ir.const import MODEL_ATOMBERG, MODEL_T10


def test_command_byte_lookup_superfan():
    assert SuperfanNEC.get_command_byte("Power", MODEL_T10) == 0x98
    assert SuperfanNEC.get_command_byte("1", MODEL_T10) == 0x94
    assert SuperfanNEC.get_command_byte("Low", MODEL_T10) == 0x94
    assert SuperfanNEC.get_command_byte("Medium", MODEL_T10) == 0x95
    assert SuperfanNEC.get_command_byte("High", MODEL_T10) == 0x96

    with pytest.raises(ValueError):
        SuperfanNEC.get_command_byte("NonExistentCommand", MODEL_T10)


def test_command_byte_lookup_atomberg():
    assert SuperfanNEC.get_command_byte("Power", MODEL_ATOMBERG) == 0x6E
    assert SuperfanNEC.get_command_byte("1", MODEL_ATOMBERG) == 0x74
    assert SuperfanNEC.get_command_byte("Boost", MODEL_ATOMBERG) == 0x70
    assert SuperfanNEC.get_command_byte("Sleep Mode", MODEL_ATOMBERG) == 0x71
    assert SuperfanNEC.get_command_byte("Timer", MODEL_ATOMBERG) == 0x69
    assert SuperfanNEC.get_command_byte("LED Light", MODEL_ATOMBERG) == 0x68


def test_raw_timings_structure():
    timings = SuperfanNEC.get_raw_timings("Power", MODEL_ATOMBERG)
    assert len(timings) == 68
    assert timings[0] == NEC_HDR_MARK
    assert timings[1] == NEC_HDR_SPACE


def test_tuya_base64_decoding():
    b64 = SuperfanNEC.get_tuya_base64("Power", MODEL_ATOMBERG)
    assert b64.startswith("b64:")
    raw_bytes = base64.b64decode(b64[4:])
    assert len(raw_bytes) == 68 * 2


def test_broadlink_base64_encoding():
    b64 = SuperfanNEC.get_broadlink_base64("Power", MODEL_ATOMBERG)
    raw = base64.b64decode(b64)
    assert raw[0] == 0x26  # Broadlink IR type
    assert raw[1] == 0x00  # Repeat count
    length = unpack("<H", raw[2:4])[0]
    assert len(raw[4:]) == length


def test_pronto_hex_encoding():
    pronto = SuperfanNEC.get_pronto_hex("Power", MODEL_ATOMBERG)
    words = pronto.split()
    assert len(words) == 4 + 68  # 4-word header + 68 timings
    assert words[0] == "0000"    # Learned format
    assert words[1] == "006D"    # 38kHz frequency code
    assert words[2] == "0022"    # 34 burst pairs (68 durations)
    assert words[3] == "0000"    # Lead-out burst


def test_esphome_and_tasmota_payloads():
    esphome = SuperfanNEC.get_esphome_timings("Boost", MODEL_ATOMBERG)
    assert len(esphome) == 68
    assert esphome[0] > 0
    assert esphome[1] < 0

    tasmota_at = SuperfanNEC.get_tasmota_payload("Power", MODEL_ATOMBERG)
    assert tasmota_at["Data"] == "0xF3006E91"


def test_nec_decoding():
    assert SuperfanNEC.decode_nec(SUPERFAN_ADDRESS, 0x98) == "Power"
    assert SuperfanNEC.decode_nec(ATOMBERG_ADDRESS, 0x6E) == "Power"
    assert SuperfanNEC.decode_nec(ATOMBERG_ADDRESS, 0x70) == "Boost"
