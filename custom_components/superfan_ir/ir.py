"""Superfan & Atomberg 32-Bit NEC Infrared Protocol Engine.

Supports 38kHz NEC protocol across Indian BLDC fan manufacturers:
- Superfan (T10 & T12/6): 16-bit address 0x00DF
- Atomberg (Renesa, Efficio, Aris, Studio): 16-bit address 0xF300

Multi-Format IR Transports:
- Home Assistant Native Infrared (Raw durations)
- ESPHome signed timing arrays (+pulse, -space)
- Broadlink Base64 (0x26 packet format)
- Tuya Base64 (little-endian uint16 durations)
- Pronto Hex (CCF format)
- Tasmota MQTT JSON (NEC 32-bit hex)
"""
from __future__ import annotations

import base64
import struct
from typing import Any

from .const import MODEL_ATOMBERG

# Standard 38kHz NEC timing constants (in microseconds)
NEC_HDR_MARK = 9000
NEC_HDR_SPACE = 4500
NEC_BIT_MARK = 560
NEC_ONE_SPACE = 1690
NEC_ZERO_SPACE = 560
NEC_RPT_SPACE = 2250

SUPERFAN_ADDRESS = 0x00DF
ATOMBERG_ADDRESS = 0xF300

# Superfan Command byte lookup table
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
    0x94: "Low",          # Also Speed 1 / Eco
    0x99: "2",
    0x95: "Medium",       # Also Speed 3
    0x9A: "4",
    0x96: "High",         # Also Speed 5
    0x9F: "2 Hour Timer",
    0x9B: "6 Hour Timer",
    0x9E: "Breeze Mode",
    0x9C: "Speed Adjust",
    0x91: "Wellness Mode",
    0x8C: "Reverse Mode",
    0x8D: "AC Mix",
}

# Atomberg Command byte lookup table (Hardware verified)
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


class SuperfanNEC:
    """Encoder and decoder for Superfan and Atomberg NEC IR signals."""

    @staticmethod
    def get_address(model: str | None = None) -> int:
        """Get the 16-bit NEC address for the model."""
        if model == MODEL_ATOMBERG or model == "Atomberg":
            return ATOMBERG_ADDRESS
        return SUPERFAN_ADDRESS

    @staticmethod
    def get_command_byte(command_name: str, model: str | None = None) -> int:
        """Get the 8-bit command byte for a command name and model."""
        if model == MODEL_ATOMBERG or model == "Atomberg":
            if command_name not in ATOMBERG_COMMAND_BYTES:
                raise ValueError(f"Unknown Atomberg command: {command_name}")
            return ATOMBERG_COMMAND_BYTES[command_name]

        if command_name not in SUPERFAN_COMMAND_BYTES:
            raise ValueError(f"Unknown Superfan command: {command_name}")
        return SUPERFAN_COMMAND_BYTES[command_name]

    @classmethod
    def get_raw_timings(cls, command_name: str, model: str | None = None) -> list[int]:
        """Generate alternating microsecond durations [pulse, space, pulse, ...] for Home Assistant RawIRCommand."""
        cmd_byte = cls.get_command_byte(command_name, model)
        addr = cls.get_address(model)
        inv_cmd = (~cmd_byte) & 0xFF

        # 32 bits transmitted LSB-first:
        # Byte 0: Address Low
        # Byte 1: Address High
        # Byte 2: Command
        # Byte 3: Inverted Command
        bytes_to_send = [addr & 0xFF, (addr >> 8) & 0xFF, cmd_byte, inv_cmd]

        timings: list[int] = [NEC_HDR_MARK, NEC_HDR_SPACE]

        for b in bytes_to_send:
            for bit_idx in range(8):
                bit = (b >> bit_idx) & 1
                timings.append(NEC_BIT_MARK)
                timings.append(NEC_ONE_SPACE if bit else NEC_ZERO_SPACE)

        # Final stop bit and space
        timings.append(NEC_BIT_MARK)
        timings.append(30000)

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
            # Broadlink ticks (~30.5 microseconds per tick)
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
    def get_esphome_timings(cls, command_name: str, model: str | None = None) -> list[int]:
        """Generate signed ESPHome pulse/space timing array (+pulse, -space)."""
        timings = cls.get_raw_timings(command_name, model)
        return [t if i % 2 == 0 else -t for i, t in enumerate(timings)]

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
        return None


# Backward-compatible alias
COMMAND_BYTES = SUPERFAN_COMMAND_BYTES
