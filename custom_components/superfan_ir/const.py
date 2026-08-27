"""Constants for the Superfan & Multi-Brand BLDC Fan IR integration."""

DOMAIN = "superfan_ir"

CONF_FAN_MODEL = "fan_model"
CONF_IR_FORMAT = "ir_format"
CONF_BACKEND = "backend"  # Backward compatibility
CONF_EMITTER_ENTITY_ID = "emitter_entity_id"
CONF_RECEIVER_ENTITY_ID = "receiver_entity_id"
CONF_POWER_SWITCH = "power_switch"

MODEL_T10 = "SuperfanT10"
MODEL_T12_6 = "SuperfanT12/6"
MODEL_ATOMBERG = "Atomberg"
MODEL_ACTIVA = "Activa"
MODEL_ORIENT = "Orient"
MODEL_GOLDMEDAL = "Goldmedal"

MODEL_OPTIONS = {
    MODEL_ATOMBERG: "Atomberg BLDC (Renesa, Efficio, Aris, Studio, Erica Series)",
    MODEL_T10: "Superfan T10 (Super X, A, V, J, P, Visree Series)",
    MODEL_T12_6: "Superfan T12/6 (Super Q Series)",
    MODEL_ACTIVA: "Activa BLDC (Gracia, Energia, Apsara Series)",
    MODEL_ORIENT: "Orient BLDC (I-Tome, Aeroslim, Wendy, Ecotech Series)",
    MODEL_GOLDMEDAL: "Goldmedal BLDC (Opus Prime, Winzo, Spacio, Aura Lux Series)",
}

FAN_MODELS = list(MODEL_OPTIONS.keys())

IR_FORMAT_AUTO = "auto"
IR_FORMAT_RAW = "raw"
IR_FORMAT_BROADLINK = "broadlink"
IR_FORMAT_TUYA = "tuya"
IR_FORMAT_PRONTO = "pronto"
IR_FORMAT_TASMOTA = "tasmota"

IR_FORMAT_OPTIONS = {
    IR_FORMAT_AUTO: "Auto-Detect (Recommended)",
    IR_FORMAT_RAW: "Home Assistant Infrared / ESPHome (Hardware-Tested & Confirmed)",
    IR_FORMAT_BROADLINK: "Broadlink Base64 (Format Verified)",
    IR_FORMAT_TUYA: "Tuya Base64 (Format Verified)",
    IR_FORMAT_PRONTO: "Pronto Hex (Universal Format)",
    IR_FORMAT_TASMOTA: "Tasmota / NEC Hex (MQTT Format)",
}

# Backward compatibility
BACKEND_REMOTE = "Legacy Remote (Tuya)"
BACKEND_INFRARED = "Native Infrared"
BACKEND_ESPHOME = "ESPHome (Raw API Service)"
BACKENDS = [BACKEND_REMOTE, BACKEND_INFRARED, BACKEND_ESPHOME]
