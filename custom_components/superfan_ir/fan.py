import asyncio
import logging
from typing import Any
import voluptuous as vol

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_platform
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.const import STATE_ON, STATE_OFF
from homeassistant.core import Event

from .const import DOMAIN, CONF_FAN_MODEL, CONF_BACKEND, CONF_EMITTER_ENTITY_ID, MODEL_T10, MODEL_T12_6, BACKEND_REMOTE, BACKEND_INFRARED, CONF_POWER_SWITCH

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up the Superfan from a config entry."""
    codes = hass.data[DOMAIN].get("codes", {})
    model = entry.data.get(CONF_FAN_MODEL)
    backend = entry.data.get(CONF_BACKEND)
    
    model_codes = codes.get(model, {})
    
    async_add_entities([SuperfanIRNative(entry, model, backend, model_codes)])
    
    platform = entity_platform.async_get_current_platform()
    
    platform.async_register_entity_service(
        "speed_adjust",
        {},
        "async_speed_adjust"
    )
    
    platform.async_register_entity_service(
        "set_timer",
        {
            vol.Required("duration"): vol.In([2, 6])
        },
        "async_set_timer"
    )

class SuperfanIRNative(FanEntity, RestoreEntity):
    """Superfan IR Entity."""

    _attr_assumed_state = True

    def __init__(self, entry: ConfigEntry, model: str, backend: str, codes: dict):
        self._entry = entry
        self._attr_name = entry.title
        self._attr_unique_id = entry.entry_id
        self._model = model
        self._backend = backend
        self._codes = codes
        
        self._attr_is_on = False
        self._attr_percentage = None
        self._attr_preset_mode = None
        
        if self._model == MODEL_T10:
            self._attr_preset_modes = ["Breeze Mode", "Speed Adjust", "2 Hour Timer", "6 Hour Timer"]
            self._attr_supported_features = (
                FanEntityFeature.SET_SPEED |
                FanEntityFeature.TURN_ON |
                FanEntityFeature.TURN_OFF |
                FanEntityFeature.PRESET_MODE
            )
            self._attr_speed_count = 5
        else:
            self._attr_preset_modes = ["Breeze Mode", "Speed Adjust", "2hr Timer", "6hr Timer", "Eco Mode", "Wellness Mode", "AC Mix"]
            self._attr_supported_features = (
                FanEntityFeature.SET_SPEED |
                FanEntityFeature.TURN_ON |
                FanEntityFeature.TURN_OFF |
                FanEntityFeature.PRESET_MODE |
                FanEntityFeature.DIRECTION
            )
            self._attr_speed_count = 3

    @property
    def _emitter_id(self) -> str | None:
        return self._entry.options.get(CONF_EMITTER_ENTITY_ID, self._entry.data.get(CONF_EMITTER_ENTITY_ID))

    async def async_added_to_hass(self):
        """Restore state and listen for switch changes."""
        await super().async_added_to_hass()
        
        # Restore previous state
        last_state = await self.async_get_last_state()
        if last_state is not None:
            self._attr_is_on = last_state.state == STATE_ON
            if "percentage" in last_state.attributes:
                self._attr_percentage = last_state.attributes["percentage"]
            if "preset_mode" in last_state.attributes:
                self._attr_preset_mode = last_state.attributes["preset_mode"]

        # Track power switch changes
        if self._power_switch:
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass, [self._power_switch], self._async_switch_changed
                )
            )

    async def _async_switch_changed(self, event: Event):
        """Handle physical power switch state changes."""
        new_state = event.data.get("new_state")
        if new_state is None:
            return
            
        if new_state.state == STATE_OFF:
            self._attr_is_on = False
            self._attr_percentage = 0
            self._attr_preset_mode = None
        elif new_state.state == STATE_ON and not self._attr_is_on:
            self._attr_is_on = True
            if not self._attr_percentage:
                self._attr_percentage = 33 if self._model == MODEL_T12_6 else 20
                
        self.async_write_ha_state()

    @property
    def _power_switch(self) -> str | None:
        return self._entry.options.get(CONF_POWER_SWITCH)

    async def _ensure_power(self) -> None:
        """Ensure the power switch is turned on before sending an IR command."""
        if not self._power_switch:
            return

        switch_state = self.hass.states.get(self._power_switch)
        if switch_state and switch_state.state == "on":
            return

        # Turn on the smart switch
        await self.hass.services.async_call(
            "switch",
            "turn_on",
            {"entity_id": self._power_switch},
            context=self._context
        )
        
        # We assume a 2-second delay is needed for the fan's board to boot up and accept IR commands.
        await asyncio.sleep(2.0)

    async def _send_ir_command(self, code_key: str):
        """Send IR command using the appropriate backend."""
        tuya_b64 = self._codes.get(code_key)
        if not tuya_b64:
            _LOGGER.error("Code not found for key: %s", code_key)
            return

        payload = tuya_b64 if tuya_b64.startswith("b64:") else f"b64:{tuya_b64}"

        if self._backend == BACKEND_REMOTE:
            domain = "remote"
            service = "send_command"
            service_data = {
                "entity_id": self._emitter_id,
                "command": [payload],
            }
            await self.hass.services.async_call(
                domain,
                service,
                service_data,
                context=self._context
            )
        elif self._backend == "ESPHome (Raw API Service)":
            try:
                from .utils import decode_tuya_to_raw
                raw_timings = decode_tuya_to_raw(tuya_b64)
                
                # Assume emitter_id contains the ESPHome device name, e.g. "ir_blaster"
                device_name = self._emitter_id.replace("esphome.", "").strip()
                service_name = f"{device_name}_transmit_raw" if not device_name.endswith("_transmit_raw") else device_name
                
                await self.hass.services.async_call(
                    "esphome",
                    service_name,
                    {"command": raw_timings},
                    context=self._context
                )
            except Exception as e:
                _LOGGER.error("Failed to send IR command via ESPHome service: %s", e)
        else:
            try:
                from .utils import decode_tuya_to_raw, RawIRCommand
                from homeassistant.components.infrared.helpers import async_send_command
                
                raw_timings = decode_tuya_to_raw(tuya_b64)
                command = RawIRCommand(raw_timings)
                
                await async_send_command(self.hass, self._emitter_id, command)
            except Exception as e:
                _LOGGER.error("Failed to send IR command via native infrared: %s", e)

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Turn on the fan."""
        await self._ensure_power()
        
        if percentage is None and preset_mode is None:
            await self._send_ir_command("Power")
            self._attr_is_on = True
            # HA requires a non-zero percentage when on. Default to a valid low speed if 0.
            if not self._attr_percentage:
                self._attr_percentage = 33 if self._model == MODEL_T12_6 else 20
        if percentage is not None:
            await self.async_set_percentage(percentage)
        if preset_mode is not None:
            await self.async_set_preset_mode(preset_mode)
            
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the fan."""
        if self._power_switch:
            # User specified to only turn off the smart switch, not the actual fan via IR
            await self.hass.services.async_call(
                "switch",
                "turn_off",
                {"entity_id": self._power_switch},
                context=self._context
            )
        else:
            await self._send_ir_command("Power")
            
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
        self._attr_is_on = True
        self._attr_percentage = percentage
        self._attr_preset_mode = None

        if self._model == MODEL_T10:
            if percentage <= 20:
                key = "1"
            elif percentage <= 40:
                key = "2"
            elif percentage <= 60:
                key = "3"
            elif percentage <= 80:
                key = "4"
            else:
                key = "5"
        else:
            if percentage <= 33:
                key = "Low"
            elif percentage <= 66:
                key = "Medium"
            else:
                key = "High"

        await self._send_ir_command(key)
        self.async_write_ha_state()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        if preset_mode not in self._attr_preset_modes:
            return
            
        await self._ensure_power()
        self._attr_is_on = True
        self._attr_preset_mode = preset_mode
        self._attr_percentage = None
        await self._send_ir_command(preset_mode)
        self.async_write_ha_state()

    async def async_set_direction(self, direction: str) -> None:
        """Set the direction of the fan."""
        if self._model != MODEL_T12_6:
            return
        
        await self._ensure_power()
        if direction == "reverse":
            await self._send_ir_command("Reverse Mode")

    async def async_speed_adjust(self) -> None:
        """Cycle speed."""
        await self._ensure_power()
        await self._send_ir_command("Speed Adjust")

    async def async_set_timer(self, duration: int) -> None:
        """Set the timer."""
        await self._ensure_power()
        if duration == 2:
            key = "2hr Timer" if self._model == MODEL_T12_6 else "2 Hour Timer"
            await self._send_ir_command(key)
        elif duration == 6:
            key = "6hr Timer" if self._model == MODEL_T12_6 else "6 Hour Timer"
            await self._send_ir_command(key)