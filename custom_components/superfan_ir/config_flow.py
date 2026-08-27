"""Config flow and Options flow for Superfan & Atomberg fan integration."""
from __future__ import annotations

from typing import Any
import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_EMITTER_ENTITY_ID,
    CONF_FAN_MODEL,
    CONF_IR_FORMAT,
    CONF_POWER_SWITCH,
    CONF_RECEIVER_ENTITY_ID,
    DOMAIN,
    IR_FORMAT_AUTO,
    IR_FORMAT_OPTIONS,
    MODEL_OPTIONS,
    MODEL_T10,
)


def _get_model_select_options() -> list[selector.SelectOptionDict]:
    return [
        selector.SelectOptionDict(
            value=key,
            label=label,
        )
        for key, label in MODEL_OPTIONS.items()
    ]


def _get_ir_format_select_options() -> list[selector.SelectOptionDict]:
    return [
        selector.SelectOptionDict(
            value=key,
            label=label,
        )
        for key, label in IR_FORMAT_OPTIONS.items()
    ]


class SuperfanConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Superfan & Atomberg fan integration."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize config flow."""
        self.data: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial user setup step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self.data.update(user_input)
            return await self.async_step_emitter()

        data_schema = vol.Schema({
            vol.Required("name", default="Living Room Fan"): selector.TextSelector(
                selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
            ),
            vol.Required(CONF_FAN_MODEL, default=MODEL_T10): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=_get_model_select_options(),
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(CONF_IR_FORMAT, default=IR_FORMAT_AUTO): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=_get_ir_format_select_options(),
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
        })

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    async def async_step_emitter(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle selecting transmitter entity."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self.data.update(user_input)
            return self.async_create_entry(title=self.data["name"], data=self.data)

        ir_fmt = self.data.get(CONF_IR_FORMAT, IR_FORMAT_AUTO)
        if ir_fmt in ("raw", "auto"):
            emitter_selector = selector.EntitySelector(
                selector.EntitySelectorConfig(domain=["infrared", "remote"])
            )
        else:
            emitter_selector = selector.EntitySelector(
                selector.EntitySelectorConfig(domain="remote")
            )

        data_schema = vol.Schema({
            vol.Required(CONF_EMITTER_ENTITY_ID): emitter_selector,
        })

        return self.async_show_form(
            step_id="emitter",
            data_schema=data_schema,
            description_placeholders={"name": self.data.get("name", "Fan")},
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow for this handler."""
        return SuperfanOptionsFlow(config_entry)


class SuperfanOptionsFlow(OptionsFlow):
    """Handle options for Superfan & Atomberg fans."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_model = self._config_entry.options.get(
            CONF_FAN_MODEL,
            self._config_entry.data.get(CONF_FAN_MODEL, MODEL_T10),
        )
        current_fmt = self._config_entry.options.get(
            CONF_IR_FORMAT,
            self._config_entry.data.get(CONF_IR_FORMAT, IR_FORMAT_AUTO),
        )
        current_emitter = self._config_entry.options.get(
            CONF_EMITTER_ENTITY_ID,
            self._config_entry.data.get(CONF_EMITTER_ENTITY_ID),
        )
        current_receiver = self._config_entry.options.get(
            CONF_RECEIVER_ENTITY_ID,
            self._config_entry.data.get(CONF_RECEIVER_ENTITY_ID, ""),
        )
        current_switch = self._config_entry.options.get(
            CONF_POWER_SWITCH,
            self._config_entry.data.get(CONF_POWER_SWITCH, ""),
        )

        schema = vol.Schema({
            vol.Required(CONF_FAN_MODEL): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=_get_model_select_options(),
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(CONF_IR_FORMAT): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=_get_ir_format_select_options(),
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(CONF_EMITTER_ENTITY_ID): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=["infrared", "remote"])
            ),
            vol.Optional(CONF_RECEIVER_ENTITY_ID): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=["sensor", "remote"])
            ),
            vol.Optional(CONF_POWER_SWITCH): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="switch")
            ),
        })

        suggested = {
            CONF_FAN_MODEL: current_model,
            CONF_IR_FORMAT: current_fmt,
            CONF_EMITTER_ENTITY_ID: current_emitter,
            CONF_RECEIVER_ENTITY_ID: current_receiver,
            CONF_POWER_SWITCH: current_switch,
        }
        schema = self.add_suggested_values_to_schema(schema, suggested)

        return self.async_show_form(step_id="init", data_schema=schema)
