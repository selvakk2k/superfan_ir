"""Constants for the Superfan IR Native integration."""

DOMAIN = "superfan_ir"

CONF_FAN_MODEL = "fan_model"
CONF_BACKEND = "backend"
CONF_EMITTER_ENTITY_ID = "emitter_entity_id"

MODEL_T10 = "SuperfanT10"
MODEL_T12_6 = "SuperfanT12/6"

MODEL_OPTIONS = {
    MODEL_T10: "Superfan T10 Remote (Models: Super X, A, V, J, P, Visree T6 & P6)",
    MODEL_T12_6: "Superfan T12/6 Remote (Models: Super Q Series)"
}

FAN_MODELS = list(MODEL_OPTIONS.keys())

BACKEND_REMOTE = "Legacy Remote (Tuya)"
BACKEND_INFRARED = "Native Infrared"
BACKENDS = [BACKEND_REMOTE, BACKEND_INFRARED]

CONF_POWER_SWITCH = "power_switch"
