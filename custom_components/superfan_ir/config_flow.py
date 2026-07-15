import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import DOMAIN, CONF_FAN_MODEL, CONF_BACKEND, CONF_EMITTER_ENTITY_ID, FAN_MODELS, BACKENDS, BACKEND_REMOTE, BACKEND_INFRARED, MODEL_OPTIONS, CONF_POWER_SWITCH

class SuperfanConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Superfan IR Native."""

    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self.data = {}

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            self.data.update(user_input)
            return await self.async_step_emitter()

        data_schema = vol.Schema({
            vol.Required("name"): str,
            vol.Required(CONF_FAN_MODEL, default=FAN_MODELS[0]): vol.In(MODEL_OPTIONS),
            vol.Required(CONF_BACKEND, default=BACKENDS[1]): vol.In(BACKENDS),
        })

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    async def async_step_emitter(self, user_input=None):
        """Handle the emitter selection step."""
        errors = {}

        if user_input is not None:
            self.data.update(user_input)
            return self.async_create_entry(title=self.data["name"], data=self.data)

        # Determine domain filter based on backend choice
        domain_filter = "remote" if self.data[CONF_BACKEND] == BACKEND_REMOTE else "infrared"

        data_schema = vol.Schema({
            vol.Required(CONF_EMITTER_ENTITY_ID): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=domain_filter)
            )
        })

        return self.async_show_form(
            step_id="emitter", data_schema=data_schema, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return SuperfanOptionsFlow(config_entry)


class SuperfanOptionsFlow(config_entries.OptionsFlow):
    """Handle options."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        domain_filter = "remote" if self._config_entry.data.get(CONF_BACKEND) == BACKEND_REMOTE else "infrared"

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(
                    CONF_EMITTER_ENTITY_ID,
                    default=self._config_entry.options.get(
                        CONF_EMITTER_ENTITY_ID,
                        self._config_entry.data.get(CONF_EMITTER_ENTITY_ID)
                    ),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=domain_filter)
                ),
                vol.Optional(
                    CONF_POWER_SWITCH,
                    description={"suggested_value": self._config_entry.options.get(CONF_POWER_SWITCH)}
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="switch")
                ),
            }),
        )
