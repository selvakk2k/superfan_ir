"""Multi-Brand 32-Bit NEC Infrared Protocol Engine for Indian BLDC Ceiling Fans.

Hardware-Verified 38kHz NEC Carrier Protocols:
- Superfan (T10 & T12/6): 16-bit address 0x00DF
- Atomberg (Renesa, Efficio, Aris, Studio): 16-bit address 0xF300
- Activa (Gracia, Energia, Apsara Series): 16-bit address 0x5AA5
- Orient Electric (I-Tome, Aeroslim, Wendy, Ecotech): 16-bit address 0x6B94
- Goldmedal (Opus Prime, Winzo, Spacio, Aura Lux): 16-bit address 0x5A95

Transports Supported:
- Home Assistant Native Infrared (Raw duration microsecond arrays via infrared.*)
- Broadlink Base64 (0x26 packet format)
- Tuya Base64 (little-endian uint16 byte stream)
- Pronto Hex (Universal CCF 0000 006D format)
- Tasmota MQTT JSON (NEC 32-bit hex)
"""
from __future__ import annotations

import base64
import struct
from typing import Any

from .const import (
    MODEL_ACTIVA,
    MODEL_ATOMBERG,
    MODEL_GOLDMEDAL,
    MODEL_ORIENT,
    MODEL_T10,
    MODEL_T12_6,
)

# Standard 38kHz NEC timing constants (in microseconds)
NEC_HDR_MARK = 9000
NEC_HDR_SPACE = 4500
NEC_BIT_MARK = 560
NEC_ONE_SPACE = 1690
NEC_ZERO_SPACE = 560
NEC_RPT_SPACE = 2250

SUPERFAN_ADDRESS = 0x00DF
ATOMBERG_ADDRESS = 0xF300
ACTIVA_ADDRESS = 0x5AA5
ORIENT_ADDRESS = 0x6B94
GOLDMEDAL_ADDRESS = 0x5A95

# 1. Superfan Command Bytes
SUPERFAN_COMMAND_BYTES: dict[str, int] = {
    "Power": 0x98,
    "1": 0x94,
    "2": 0x99,
    "3": 0x95,
    "4": 0x9A,
    "5": 0x96,
    "Low": 0x94,
    "Medium": 0x95,
    "High": 0x96,
    "Eco Mode": 0x94,
    "Sleep Mode": 0x94,
    "2 Hour Timer": 0x9F,
    "2hr Timer": 0x9F,
    "6 Hour Timer": 0x9B,
    "6hr Timer": 0x9B,
    "Breeze Mode": 0x9E,
    "Speed Adjust": 0x9C,
    "Wellness Mode": 0x91,
    "Reverse Mode": 0x8C,
    "AC Mix": 0x8D,
}

SUPERFAN_BYTE_TO_COMMAND: dict[int, str] = {
    0x98: "Power",
    0x94: "Low",
    0x99: "2",
    0x95: "Medium",
    0x9A: "4",
    0x96: "High",
    0x9F: "2 Hour Timer",
    0x9B: "6 Hour Timer",
    0x9E: "Breeze Mode",
    0x9C: "Speed Adjust",
    0x91: "Wellness Mode",
    0x8C: "Reverse Mode",
    0x8D: "AC Mix",
}

# 2. Atomberg Command Bytes (Hardware verified)
ATOMBERG_COMMAND_BYTES: dict[str, int] = {
    "Power": 0x6E,
    "1": 0x74,
    "2": 0x6F,
    "3": 0x75,
    "4": 0x6C,
    "5": 0x77,
    "6": 0x70,
    "Boost": 0x70,
    "Sleep Mode": 0x71,
    "Sleep": 0x71,
    "Timer": 0x69,
    "LED Light": 0x68,
    "LED": 0x68,
    "Light": 0x68,
}

ATOMBERG_BYTE_TO_COMMAND: dict[int, str] = {
    0x6E: "Power",
    0x74: "1",
    0x6F: "2",
    0x75: "3",
    0x6C: "4",
    0x77: "5",
    0x70: "Boost",
    0x71: "Sleep Mode",
    0x69: "Timer",
    0x68: "LED Light",
}

# 3. Activa Command Bytes (Hardware verified 0x5AA5)
ACTIVA_COMMAND_BYTES: dict[str, int] = {
    "Power": 0xEA,
    "1": 0x4A,
    "2": 0xCA,
    "3": 0x00,
    "4": 0xBA,
    "5": 0x18,
    "6": 0xD8,
    "Boost": 0x62,
    "Nature Mode": 0x98,
    "Smart Mode": 0xF8,
    "LED Light": 0x38,
    "Reverse Mode": 0x48,
    "Timer 2 Hours": 0x78,
    "Timer 4 Hours": 0xF2,
    "Timer 8 Hours": 0x32,
    "Timer Off": 0xB8,
}

ACTIVA_BYTE_TO_COMMAND: dict[int, str] = {
    0xEA: "Power",
    0x4A: "1",
    0xCA: "2",
    0x00: "3",
    0xBA: "4",
    0x18: "5",
    0xD8: "6",
    0x62: "Boost",
    0x98: "Nature Mode",
    0xF8: "Smart Mode",
    0x38: "LED Light",
    0x48: "Reverse Mode",
    0x78: "Timer 2 Hours",
    0xF2: "Timer 4 Hours",
    0x32: "Timer 8 Hours",
    0xB8: "Timer Off",
}

# 4. Orient Command Bytes (Hardware verified 0x6B94)
ORIENT_COMMAND_BYTES: dict[str, int] = {
    "Power": 0x52,
    "Power Off": 0x52,
    "Power On": 0xAA,
    "1": 0x7A,
    "2": 0xFA,
    "3": 0x3A,
    "4": 0xBA,
    "5": 0x4A,
    "Boost": 0xF2,
    "Speed Adjust": 0x9A,
    "LED Light": 0x92,
    "Timer 2 Hours": 0x2A,
    "Timer 4 Hours": 0x32,
    "Timer 6 Hours": 0xD2,
}

ORIENT_BYTE_TO_COMMAND: dict[int, str] = {
    0x52: "Power Off",
    0xAA: "Power On",
    0x7A: "1",
    0xFA: "2",
    0x3A: "3",
    0xBA: "4",
    0x4A: "5",
    0xF2: "Boost",
    0x9A: "Speed Adjust",
    0x92: "LED Light",
    0x2A: "Timer 2 Hours",
    0x32: "Timer 4 Hours",
    0xD2: "Timer 6 Hours",
}

# 5. Goldmedal Command Bytes (Hardware verified 0x5A95)
GOLDMEDAL_COMMAND_BYTES: dict[str, int] = {
    "Power": 0x33,
    "1": 0xB3,
    "2": 0x8B,
    "3": 0x53,
    "4": 0x0B,
    "5": 0x93,
    "Boost": 0x4B,
    "Sleep Mode": 0xAB,
    "LED Light": 0xD3,
    "Timer 1 Hour": 0x2B,
    "Timer 2 Hours": 0xFB,
    "Timer 3 Hours": 0x3B,
    "Timer 6 Hours": 0x13,
    "Timer Off": 0x6B,
}

GOLDMEDAL_BYTE_TO_COMMAND: dict[int, str] = {
    0x33: "Power",
    0xB3: "1",
    0x8B: "2",
    0x53: "3",
    0x0B: "4",
    0x93: "5",
    0x4B: "Boost",
    0xAB: "Sleep Mode",
    0xD3: "LED Light",
    0x2B: "Timer 1 Hour",
    0xFB: "Timer 2 Hours",
    0x3B: "Timer 3 Hours",
    0x13: "Timer 6 Hours",
    0x6B: "Timer Off",
}


class SuperfanNEC:
    """Encoder and decoder for Indian BLDC fan NEC IR signals."""

    @staticmethod
    def get_address(model: str | None = None) -> int:
        """Get the 16-bit NEC address for the model."""
        if model == MODEL_ATOMBERG or model == "Atomberg":
            return ATOMBERG_ADDRESS
        if model == MODEL_ACTIVA or model == "Activa":
            return ACTIVA_ADDRESS
        if model == MODEL_ORIENT or model == "Orient":
            return ORIENT_ADDRESS
        if model == MODEL_GOLDMEDAL or model == "Goldmedal":
            return GOLDMEDAL_ADDRESS
        return SUPERFAN_ADDRESS

    @staticmethod
    def get_command_byte(command_name: str, model: str | None = None) -> int:
        """Get the 8-bit command byte for a command name and model."""
        if model == MODEL_ATOMBERG or model == "Atomberg":
            if command_name not in ATOMBERG_COMMAND_BYTES:
                raise ValueError(f"Unknown Atomberg command: {command_name}")
            return ATOMBERG_COMMAND_BYTES[command_name]

        if model == MODEL_ACTIVA or model == "Activa":
            if command_name not in ACTIVA_COMMAND_BYTES:
                raise ValueError(f"Unknown Activa command: {command_name}")
            return ACTIVA_COMMAND_BYTES[command_name]

        if model == MODEL_ORIENT or model == "Orient":
            if command_name not in ORIENT_COMMAND_BYTES:
                raise ValueError(f"Unknown Orient command: {command_name}")
            return ORIENT_COMMAND_BYTES[command_name]

        if model == MODEL_GOLDMEDAL or model == "Goldmedal":
            if command_name not in GOLDMEDAL_COMMAND_BYTES:
                raise ValueError(f"Unknown Goldmedal command: {command_name}")
            return GOLDMEDAL_COMMAND_BYTES[command_name]

        if command_name not in SUPERFAN_COMMAND_BYTES:
            raise ValueError(f"Unknown Superfan command: {command_name}")
        return SUPERFAN_COMMAND_BYTES[command_name]

    @classmethod
    def get_raw_timings(cls, command_name: str, model: str | None = None, repeats: int = 2) -> list[int]:
        """Generate alternating microsecond durations [pulse, space, ...] for Home Assistant RawIRCommand with repeated NEC frames."""
        cmd_byte = cls.get_command_byte(command_name, model)
        addr = cls.get_address(model)
        inv_cmd = (~cmd_byte) & 0xFF

        # Transmit big-endian address bytes [Addr0, Addr1], then Command, then ~Command
        bytes_to_send = [(addr >> 8) & 0xFF, addr & 0xFF, cmd_byte, inv_cmd]
        timings: list[int] = []

        for rep in range(max(1, repeats)):
            timings.extend([NEC_HDR_MARK, NEC_HDR_SPACE])
            for b in bytes_to_send:
                for bit_idx in range(8):
                    bit = (b >> bit_idx) & 1
                    timings.append(NEC_BIT_MARK)
                    timings.append(NEC_ONE_SPACE if bit else NEC_ZERO_SPACE)

            # End bit of frame + lead-out gap
            timings.append(NEC_BIT_MARK)
            timings.append(42000 if rep < repeats - 1 else 30000)

        # NEC Repeat Frame (required for hardware receiver filtering on Superfan & Atomberg ICs)
        timings.extend([NEC_HDR_MARK, NEC_RPT_SPACE, NEC_BIT_MARK, 30000])
        return timings

    @classmethod
    def get_tuya_base64(cls, command_name: str, model: str | None = None) -> str:
        """Generate Tuya-compatible little-endian uint16 base64 payload."""
        timings = cls.get_raw_timings(command_name, model)
        payload = bytearray()
        for t in timings:
            payload.extend(struct.pack("<H", min(t, 65535)))
        return "b64:" + base64.b64encode(payload).decode("ascii")

    @classmethod
    def get_broadlink_base64(cls, command_name: str, model: str | None = None) -> str:
        """Generate Broadlink-compatible base64 IR payload (0x26 packet)."""
        timings = cls.get_raw_timings(command_name, model)
        payload = bytearray()
        for t in timings:
            ticks = int(round(t / 30.5))
            if ticks < 256:
                payload.append(ticks)
            else:
                payload.append(0)
                payload.extend(struct.pack(">H", min(ticks, 65535)))
        payload.append(0x0D)
        payload.append(0x05)

        header = bytearray([0x26, 0x00])
        header.extend(struct.pack("<H", len(payload)))
        return base64.b64encode(header + payload).decode("ascii")

    @classmethod
    def get_pronto_hex(cls, command_name: str, model: str | None = None, freq: int = 38000) -> str:
        """Generate Pronto Hex (CCF) format string."""
        timings = cls.get_raw_timings(command_name, model)
        timebase = 1000000.0 / freq
        pairs = len(timings) // 2
        words = [0x0000, 0x006D, pairs, 0x0000]
        for t in timings:
            cycles = int(round(t / timebase))
            words.append(min(cycles, 0xFFFF))
        return " ".join(f"{w:04X}" for w in words)



    @classmethod
    def get_tasmota_payload(cls, command_name: str, model: str | None = None) -> dict[str, Any]:
        """Generate Tasmota IR MQTT JSON payload."""
        cmd_byte = cls.get_command_byte(command_name, model)
        addr = cls.get_address(model)
        inv_cmd = (~cmd_byte) & 0xFF
        nec_hex = f"0x{addr:04X}{cmd_byte:02X}{inv_cmd:02X}"
        return {
            "Protocol": "NEC",
            "Bits": 32,
            "Data": nec_hex,
        }

    @classmethod
    def decode_nec(cls, address: int, command: int) -> str | None:
        """Decode received NEC address and command byte into action."""
        if address in (SUPERFAN_ADDRESS, 0xDF00):
            return SUPERFAN_BYTE_TO_COMMAND.get(command)
        if address in (ATOMBERG_ADDRESS, 0x00F3):
            return ATOMBERG_BYTE_TO_COMMAND.get(command)
        if address in (ACTIVA_ADDRESS, 0xA55A):
            return ACTIVA_BYTE_TO_COMMAND.get(command)
        if address in (ORIENT_ADDRESS, 0x946B):
            return ORIENT_BYTE_TO_COMMAND.get(command)
        if address in (GOLDMEDAL_ADDRESS, 0x955A):
            return GOLDMEDAL_BYTE_TO_COMMAND.get(command)
        return None


# Backward-compatible alias
COMMAND_BYTES = SUPERFAN_COMMAND_BYTES
