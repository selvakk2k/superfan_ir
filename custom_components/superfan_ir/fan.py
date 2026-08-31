"""Platform for Superfan & Multi-Brand BLDC Fan integration."""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    CONF_EMITTER_ENTITY_ID,
    CONF_FAN_MODEL,
    CONF_IR_FORMAT,
    CONF_POWER_SWITCH,
    CONF_RECEIVER_ENTITY_ID,
    DOMAIN,
    IR_FORMAT_AUTO,
    IR_FORMAT_BROADLINK,
    IR_FORMAT_PRONTO,
    IR_FORMAT_RAW,
    IR_FORMAT_TASMOTA,
    IR_FORMAT_TUYA,
    MODEL_ACTIVA,
    MODEL_ATOMBERG,
    MODEL_GOLDMEDAL,
    MODEL_ORIENT,
    MODEL_T10,
    MODEL_T12_6,
)
from .ir import SuperfanNEC

_LOGGER = logging.getLogger(__name__)

ATOMBERG_PRESET_MODES = ["Sleep Mode", "Timer", "LED Light"]

ACTIVA_PRESET_MODES = [
    "Nature Mode",
    "Smart Mode",
    "LED Light",
    "Reverse Mode",
    "Timer 2 Hours",
    "Timer 4 Hours",
    "Timer 8 Hours",
]

ORIENT_PRESET_MODES = [
    "LED Light",
    "Speed Adjust",
    "Timer 2 Hours",
    "Timer 4 Hours",
    "Timer 6 Hours",
]

GOLDMEDAL_PRESET_MODES = [
    "Sleep Mode",
    "LED Light",
    "Timer 1 Hour",
    "Timer 2 Hours",
    "Timer 3 Hours",
    "Timer 6 Hours",
]

SUPERFAN_T10_PRESET_MODES = [
    "Breeze Mode",
    "Eco Mode",
    "Sleep Mode",
    "2hr Timer",
    "6hr Timer",
]

SUPERFAN_T12_6_PRESET_MODES = [
    "Breeze Mode",
    "Eco Mode",
    "Sleep Mode",
    "Reverse Mode",
    "Wellness Mode",
    "AC Mix",
    "Speed Adjust",
    "2hr Timer",
    "6hr Timer",
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Fan from a config entry."""
    fan_model = entry.options.get(CONF_FAN_MODEL, entry.data.get(CONF_FAN_MODEL, MODEL_T10))
    ir_format = entry.options.get(CONF_IR_FORMAT, entry.data.get(CONF_IR_FORMAT, IR_FORMAT_AUTO))
    emitter_id = entry.options.get(
        CONF_EMITTER_ENTITY_ID, entry.data.get(CONF_EMITTER_ENTITY_ID)
    )
    receiver_id = entry.options.get(
        CONF_RECEIVER_ENTITY_ID, entry.data.get(CONF_RECEIVER_ENTITY_ID)
    )
    power_switch = entry.options.get(
        CONF_POWER_SWITCH, entry.data.get(CONF_POWER_SWITCH)
    )

    async_add_entities([
        SuperfanEntity(
            entry=entry,
            fan_model=fan_model,
            ir_format=ir_format,
            emitter_id=emitter_id,
            receiver_id=receiver_id,
            power_switch=power_switch,
        )
    ])


class SuperfanEntity(FanEntity, RestoreEntity):
    """Representation of a Superfan or Multi-Brand Indian BLDC Fan."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_supported_features = (
        FanEntityFeature.SET_SPEED
        | FanEntityFeature.PRESET_MODE
        | FanEntityFeature.TURN_OFF
        | FanEntityFeature.TURN_ON
    )

    def __init__(
        self,
        entry: ConfigEntry,
        fan_model: str,
        emitter_id: str,
        ir_format: str = IR_FORMAT_AUTO,
        receiver_id: str | None = None,
        power_switch: str | None = None,
        backend: str | None = None,
    ) -> None:
        """Initialize the fan."""
        self._entry = entry
        self._model = fan_model
        self._ir_format = ir_format
        self._emitter_id = emitter_id
        self._receiver_id = receiver_id
        self._power_switch = power_switch

        self._attr_unique_id = f"{entry.entry_id}_fan"
        self._attr_name = None

        # Determine speed count, brand name, presets based on model
        if self._model == MODEL_ATOMBERG:
            self._attr_speed_count = 6
            self._attr_preset_modes = ATOMBERG_PRESET_MODES
            default_pct = 50
            brand_name = "Atomberg"
        elif self._model == MODEL_ACTIVA:
            self._attr_speed_count = 6
            self._attr_preset_modes = ACTIVA_PRESET_MODES
            default_pct = 50
            brand_name = "Activa Appliances"
        elif self._model == MODEL_ORIENT:
            self._attr_speed_count = 5
            self._attr_preset_modes = ORIENT_PRESET_MODES
            default_pct = 60
            brand_name = "Orient Electric"
        elif self._model == MODEL_GOLDMEDAL:
            self._attr_speed_count = 5
            self._attr_preset_modes = GOLDMEDAL_PRESET_MODES
            default_pct = 60
            brand_name = "Goldmedal Electricals"
        elif self._model == MODEL_T10:
            self._attr_speed_count = 5
            self._attr_preset_modes = SUPERFAN_T10_PRESET_MODES
            default_pct = 60
            brand_name = "Versa Drives (Superfan)"
        else:
            self._attr_speed_count = 3
            self._attr_preset_modes = SUPERFAN_T12_6_PRESET_MODES
            default_pct = 66
            brand_name = "Versa Drives (Superfan)"

        self._default_pct: int = default_pct
        self._switch_turned_on_time: float = 0.0
        self._last_command_time: float = 0.0
        self._last_command_source: str = "Init"
        self._last_requested_action: str | None = None
        self._is_esphome: bool = False

        self._attr_is_on: bool = False
        self._attr_percentage: int | None = 0
        self._attr_preset_mode: str | None = None
        self._last_percentage: int = default_pct
        self._last_preset_mode: str | None = None
        self._attr_assumed_state: bool = True

        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": brand_name,
            "model": fan_model,
        }

    async def async_added_to_hass(self) -> None:
        """Restore state and register event listeners."""
        await super().async_added_to_hass()

        last_state = await self.async_get_last_state()
        if last_state:
            self._attr_is_on = last_state.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN, "off")
            if self._attr_is_on:
                self._attr_percentage = last_state.attributes.get("percentage", self._last_percentage)
                self._attr_preset_mode = last_state.attributes.get("preset_mode")
                if self._attr_percentage and self._attr_percentage > 0:
                    self._last_percentage = self._attr_percentage
                if self._attr_preset_mode:
                    self._last_preset_mode = self._attr_preset_mode
            else:
                self._attr_percentage = 0
                self._attr_preset_mode = None

        if self._emitter_id:
            from homeassistant.helpers import entity_registry as er

            ent_reg = er.async_get(self.hass)
            entry = ent_reg.async_get(self._emitter_id)
            self._is_esphome = (
                (entry is not None and entry.platform == "esphome")
                or self._emitter_id.startswith("infrared.")
                or self._emitter_id.startswith("esphome.")
            )

            self.async_on_remove(
                async_track_state_change_event(
                    self.hass, [self._emitter_id], self._async_emitter_state_changed
                )
            )

        if self._power_switch:
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass, [self._power_switch], self._async_switch_state_changed
                )
            )

        if self._receiver_id:
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass, [self._receiver_id], self._async_receiver_event
                )
            )

    @callback
    def _async_switch_state_changed(self, event: Event) -> None:
        """Handle power switch state updates."""
        new_state = event.data.get("new_state")
        if new_state is None or new_state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return

        self._notify_control_source("Mains Switch")
        self._last_command_source = "Mains Switch"
        self._last_command_time = time.monotonic()
        self._last_requested_action = None

        if new_state.state == "off":
            self._attr_is_on = False
            self._attr_percentage = 0
            self._attr_preset_mode = None
        elif new_state.state == "on" and not self._attr_is_on:
            self._switch_turned_on_time = time.monotonic()
            self._attr_is_on = True
            if self._last_preset_mode and self._last_preset_mode in self._attr_preset_modes:
                self._attr_preset_mode = self._last_preset_mode
                self._attr_percentage = None
            else:
                self._attr_percentage = (
                    self._last_percentage if self._last_percentage > 0 else self._default_pct
                )
                self._attr_preset_mode = None

        self.async_write_ha_state()

    async def _async_receiver_event(self, event: Event) -> None:
        """Decode incoming IR signal from receiver entity."""
        new_state = event.data.get("new_state")
        if new_state is None or new_state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return

        raw_val = new_state.state.strip()
        try:
            if raw_val.startswith("0x") and len(raw_val) >= 8:
                nec_val = int(raw_val, 16)
                addr = (nec_val >> 16) & 0xFFFF
                cmd = (nec_val >> 8) & 0xFF
            elif raw_val.startswith("0x"):
                addr = SuperfanNEC.get_address(self._model)
                cmd = int(raw_val, 16)
            else:
                return

            action = SuperfanNEC.decode_nec(addr, cmd)
            if not action:
                return

            _LOGGER.debug("Physical IR remote pressed for %s: %s", self._model, action)
            self._notify_control_source("IR Remote")
            self._last_command_source = "IR Remote"
            self._last_command_time = time.monotonic()
            self._last_requested_action = None

            if action == "Power":
                self._attr_is_on = not self._attr_is_on
                if self._attr_is_on:
                    self._attr_percentage = self._last_percentage
                else:
                    self._attr_percentage = 0
                    self._attr_preset_mode = None
            elif action == "Power On":
                self._attr_is_on = True
                self._attr_percentage = self._last_percentage
            elif action == "Power Off":
                self._attr_is_on = False
                self._attr_percentage = 0
                self._attr_preset_mode = None
            elif action in ("Low", "Medium", "High", "1", "2", "3", "4", "5", "6", "Boost"):
                self._attr_is_on = True
                pct = self._map_speed_to_percentage(action)
                self._attr_percentage = pct
                self._last_percentage = pct
                self._attr_preset_mode = None
            elif action in self._attr_preset_modes:
                self._attr_is_on = True
                self._attr_preset_mode = action
                self._last_preset_mode = action
                self._attr_percentage = None

            self.async_write_ha_state()
        except Exception as err:
            _LOGGER.debug("Error processing IR receiver signal '%s': %s", raw_val, err)

    async def _async_emitter_state_changed(self, event: Event) -> None:
        """Handle IR blaster emitter availability changes."""
        old_state = event.data.get("old_state")
        new_state = event.data.get("new_state")
        if new_state is None or new_state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return

        # Trigger only on the edge transition from unavailable/unknown to available
        if old_state is not None and old_state.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return

        fan_name = self.name or (self._entry.title if hasattr(self, "_entry") and self._entry else "Fan")
        elapsed = time.monotonic() - self._last_command_time
        if (
            self._last_command_source == "HA"
            and self._last_requested_action is not None
            and elapsed <= 180.0
        ):
            _LOGGER.info(
                "IR blaster %s reconnected after %.1fs — resyncing '%s' for %s",
                self._emitter_id,
                elapsed,
                self._last_requested_action,
                fan_name,
            )
            if self._is_esphome:
                await asyncio.sleep(0.3)
            action_to_send = self._last_requested_action
            self._last_requested_action = None
            await self._send_ir_command(action_to_send)
        else:
            _LOGGER.debug(
                "IR blaster %s reconnected — resync skipped (source=%s, elapsed=%.1fs, pending=%s)",
                self._emitter_id,
                self._last_command_source,
                elapsed,
                self._last_requested_action,
            )

    def _map_speed_to_percentage(self, speed_key: str) -> int:
        if self._model in (MODEL_ATOMBERG, MODEL_ACTIVA):
            map_6 = {"1": 17, "2": 33, "3": 50, "4": 67, "5": 83, "6": 100, "Boost": 100}
            return map_6.get(speed_key, 50)
        if self._model in (MODEL_T10, MODEL_ORIENT, MODEL_GOLDMEDAL):
            map_5 = {"1": 20, "2": 40, "3": 60, "4": 80, "5": 100, "Boost": 100}
            return map_5.get(speed_key, 60)
        map_t12 = {"Low": 33, "Medium": 66, "High": 100}
        return map_t12.get(speed_key, 66)

    def _map_percentage_to_speed(self, percentage: int) -> str:
        """Map percentage to discrete model-specific speed key."""
        if self._model in (MODEL_ATOMBERG, MODEL_ACTIVA):
            if percentage <= 17:
                return "1"
            if percentage <= 34:
                return "2"
            if percentage <= 50:
                return "3"
            if percentage <= 67:
                return "4"
            if percentage <= 84:
                return "5"
            return "6" if self._model == MODEL_ACTIVA else "Boost"
        if self._model in (MODEL_T10, MODEL_ORIENT, MODEL_GOLDMEDAL):
            if percentage <= 20:
                return "1"
            if percentage <= 40:
                return "2"
            if percentage <= 60:
                return "3"
            if percentage <= 80:
                return "4"
            return "5"
        if percentage <= 33:
            return "Low"
        if percentage <= 66:
            return "Medium"
        return "High"

    async def _ensure_power(self) -> None:
        """Ensure the power switch is turned on and fan MCU is boot-ready before sending an IR command."""
        if not self._power_switch:
            return

        switch_state = self.hass.states.get(self._power_switch)
        if switch_state and switch_state.state == "on":
            # If switch was turned on recently (<1.5s), wait for MCU boot grace period
            elapsed = time.monotonic() - self._switch_turned_on_time
            if elapsed < 1.5:
                await asyncio.sleep(max(0.1, 1.5 - elapsed))
            return

        await self.hass.services.async_call(
            "switch",
            "turn_on",
            {"entity_id": self._power_switch},
            context=self._context,
        )
        self._switch_turned_on_time = time.monotonic()
        await asyncio.sleep(1.5)

    def _notify_control_source(self, source: str) -> None:
        """Update shared last controlled via sensor."""
        entry_data = self.hass.data.get(DOMAIN, {}).get(self._entry.entry_id)
        if entry_data and hasattr(entry_data, "set_last_controlled_via"):
            entry_data.set_last_controlled_via(source)

    async def _send_ir_command(self, code_key: str) -> bool:
        """Send IR command using the configured format and transport backend."""
        emitter = self._emitter_id
        if not emitter:
            _LOGGER.error("No emitter entity configured for %s", self.name)
            return False

        self._notify_control_source("IR Blaster")
        try:
            fmt = self._ir_format
            addr = SuperfanNEC.get_address(self._model)
            cmd_byte = SuperfanNEC.get_command_byte(code_key, self._model)
            _LOGGER.info(
                "[Superfan IR] Dispatching '%s' for model '%s' (Addr=0x%04X, Cmd=0x%02X) via %s (Format=%s)",
                code_key,
                self._model,
                addr,
                cmd_byte,
                emitter,
                fmt,
            )

            if fmt == IR_FORMAT_AUTO:
                emitter_lower = emitter.lower()
                if emitter.startswith("esphome.") or "transmit_raw" in emitter:
                    fmt = IR_FORMAT_RAW
                elif "broadlink" in emitter_lower:
                    fmt = IR_FORMAT_BROADLINK
                elif emitter.startswith("remote."):
                    fmt = IR_FORMAT_TUYA
                else:
                    fmt = IR_FORMAT_RAW

            if fmt == IR_FORMAT_RAW and (emitter.startswith("esphome.") or "transmit_raw" in emitter):
                esphome_timings = SuperfanNEC.get_esphome_timings(code_key, self._model)
                device_name = emitter.replace("esphome.", "").strip()
                service_name = (
                    f"{device_name}_transmit_raw"
                    if not device_name.endswith("_transmit_raw")
                    else device_name
                )
                await self.hass.services.async_call(
                    "esphome",
                    service_name,
                    {"command": esphome_timings},
                    context=self._context,
                )
            elif fmt == IR_FORMAT_BROADLINK:
                payload = SuperfanNEC.get_broadlink_base64(code_key, self._model)
                await self.hass.services.async_call(
                    "remote",
                    "send_command",
                    {
                        "entity_id": emitter,
                        "command": [f"b64:{payload}" if not payload.startswith("b64:") else payload],
                        "num_repeats": 2,
                        "delay_secs": 0.1,
                    },
                    context=self._context,
                )
            elif fmt == IR_FORMAT_TUYA:
                payload = SuperfanNEC.get_tuya_base64(code_key, self._model)
                await self.hass.services.async_call(
                    "remote",
                    "send_command",
                    {
                        "entity_id": emitter,
                        "command": [payload],
                        "num_repeats": 2,
                        "delay_secs": 0.1,
                    },
                    context=self._context,
                )
            elif fmt == IR_FORMAT_PRONTO:
                pronto_payload = SuperfanNEC.get_pronto_hex(code_key, self._model)
                await self.hass.services.async_call(
                    "remote",
                    "send_command",
                    {
                        "entity_id": emitter,
                        "command": [pronto_payload],
                        "num_repeats": 2,
                        "delay_secs": 0.1,
                    },
                    context=self._context,
                )
            elif fmt == IR_FORMAT_TASMOTA:
                tasmota_payload = SuperfanNEC.get_tasmota_payload(code_key, self._model)
                await self.hass.services.async_call(
                    "remote",
                    "send_command",
                    {
                        "entity_id": emitter,
                        "command": [tasmota_payload["Data"]],
                    },
                    context=self._context,
                )
            else:
                from .utils import RawIRCommand
                from homeassistant.components.infrared.helpers import async_send_command

                raw_timings = SuperfanNEC.get_raw_timings(code_key, self._model)
                command = RawIRCommand(raw_timings)
                await async_send_command(self.hass, emitter, command)
            return True
        except Exception as err:
            _LOGGER.error("Failed to dispatch IR command (%s) for %s: %s", code_key, self._model, err)
            return False

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Turn on the fan."""
        await self._ensure_power()

        if percentage is None and preset_mode is None:
            if self._last_preset_mode and self._last_preset_mode in self._attr_preset_modes:
                target_preset = self._last_preset_mode
                self._last_command_source = "HA"
                self._last_command_time = time.monotonic()
                self._last_requested_action = target_preset
                if not await self._send_ir_command(target_preset):
                    return
                self._attr_is_on = True
                self._attr_preset_mode = target_preset
                self._attr_percentage = None
            else:
                target_pct = (
                    self._last_percentage if self._last_percentage > 0 else self._default_pct
                )
                speed_key = self._map_percentage_to_speed(target_pct)
                self._last_command_source = "HA"
                self._last_command_time = time.monotonic()
                self._last_requested_action = speed_key
                if not await self._send_ir_command(speed_key):
                    return
                self._attr_is_on = True
                self._attr_percentage = target_pct
                self._attr_preset_mode = None
        elif percentage is not None:
            await self.async_set_percentage(percentage)
            return
        elif preset_mode is not None:
            await self.async_set_preset_mode(preset_mode)
            return

        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the fan."""
        self._last_command_source = "HA"
        self._last_command_time = time.monotonic()

        if self._power_switch:
            self._last_requested_action = None
            try:
                await self.hass.services.async_call(
                    "switch",
                    "turn_off",
                    {"entity_id": self._power_switch},
                    context=self._context,
                )
            except Exception as err:
                _LOGGER.error("Failed to turn off power switch %s: %s", self._power_switch, err)
                return
        else:
            cmd = "Power Off" if self._model == MODEL_ORIENT else "Power"
            self._last_requested_action = cmd
            if not await self._send_ir_command(cmd):
                return

        self._attr_is_on = False
        self._attr_percentage = 0
        self._attr_preset_mode = None
        self.async_write_ha_state()

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the speed of the fan."""
        if percentage == 0:
            await self.async_turn_off()
            return

        await self._ensure_power()
        key = self._map_percentage_to_speed(percentage)
        self._last_command_source = "HA"
        self._last_command_time = time.monotonic()
        self._last_requested_action = key

        if not await self._send_ir_command(key):
            return

        self._attr_is_on = True
        self._attr_percentage = percentage
        self._last_percentage = percentage
        self._attr_preset_mode = None
        self._last_preset_mode = None
        self.async_write_ha_state()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        if preset_mode not in self._attr_preset_modes:
            return

        await self._ensure_power()
        self._last_command_source = "HA"
        self._last_command_time = time.monotonic()
        self._last_requested_action = preset_mode

        if not await self._send_ir_command(preset_mode):
            return

        self._attr_is_on = True
        self._attr_preset_mode = preset_mode
        self._last_preset_mode = preset_mode
        self._attr_percentage = None
        self.async_write_ha_state()

    async def async_speed_adjust(self) -> None:
        """Cycle speed."""
        await self._ensure_power()
        if self._model in (MODEL_ATOMBERG, MODEL_ACTIVA):
            current_pct = self._attr_percentage or self._last_percentage
            next_pct = 17 if current_pct >= 100 else current_pct + 17
            await self.async_set_percentage(next_pct)
        elif self._model in (MODEL_ORIENT, MODEL_T10):
            await self._send_ir_command("Speed Adjust")
        else:
            current_pct = self._attr_percentage or self._last_percentage
            next_pct = 20 if current_pct >= 100 else current_pct + 20
            await self.async_set_percentage(next_pct)

    async def async_set_timer(self, duration: int) -> None:
        """Set the timer."""
        await self._ensure_power()
        if self._model == MODEL_ATOMBERG:
            await self._send_ir_command("Timer")
        elif self._model == MODEL_ACTIVA:
            key = f"Timer {duration} Hours"
            await self._send_ir_command(key)
        elif self._model == MODEL_ORIENT:
            key = f"Timer {duration} Hours"
            await self._send_ir_command(key)
        elif self._model == MODEL_GOLDMEDAL:
            key = f"Timer {duration} Hour" if duration == 1 else f"Timer {duration} Hours"
            await self._send_ir_command(key)
        elif duration == 2:
            key = "2hr Timer" if self._model == MODEL_T12_6 else "2 Hour Timer"
            await self._send_ir_command(key)
        elif duration == 6:
            key = "6hr Timer" if self._model == MODEL_T12_6 else "6 Hour Timer"
            await self._send_ir_command(key)
