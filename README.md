# Superfan IR Native Integration (`superfan_ir`)

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![Version](https://img.shields.io/github/v/release/selvakk2k/superfan_ir)](https://github.com/selvakk2k/superfan_ir/releases)

A modern Home Assistant custom integration for controlling Superfan ceiling fans via infrared (IR) blasters. This integration supports config flows, multiple device configuration, smart switches, and is compatible with both the legacy `remote` command architecture (exclusively for Tuya-based IR blasters) and the native Home Assistant `infrared` platform.

> 💡 A dedicated Lovelace card with a premium UI is available: **[superfan-card](https://github.com/selvakk2k/superfan-card)**

---

## Remote Mappings & Compatibility

Superfan makes two primary remote control models. During configuration, select the remote type corresponding to your fan series:

### 1. Superfan T10 Remote
* **Supported Models:** Super X, A, V, J, P Series, and Visree T6 & P6 Series.
* **Features:** 5 speed tiers (mapped to 1-20%, 21-40%, 41-60%, 61-80%, and 81-100%).
* **Presets (Exposed on Fan Card):** `Breeze Mode`, `Speed Adjust`, `2 Hour Timer`, `6 Hour Timer`.

<p align="center">
  <img src="images/remote_t10.png" alt="Superfan T10 Remote" width="250"/>
</p>

### 2. Superfan T12/6 Remote
* **Supported Models:** Super Q Series.
* **Features:** 3 speed tiers (Low, Medium, High) and direction reversing (`Reverse Mode`).
* **Presets (Exposed on Fan Card):** `Breeze Mode`, `Speed Adjust`, `2hr Timer`, `6hr Timer`, `Eco Mode`, `Welness Mode`, `AC Mix`.

<p align="center">
  <img src="images/remote_t12_6.png" alt="Superfan T12/6 Remote" width="250"/>
</p>

### 3. Multi-Brand Indian BLDC Fan Support
The integration natively supports all popular Indian BLDC fan models:
* **Atomberg**: Renesa, Efficio, Aris, Studio Series (6 speeds + Boost, Sleep, Timer, LED Light)
* **Activa**: Gracia, Energia, Apsara Series (6 speeds, Nature, Smart, Reverse, Timer)
* **Orient Electric**: I-Tome, Aeroslim, Wendy, Ecotech Series (5 speeds, Timer, LED Light)
* **Goldmedal**: Opus Prime, Winzo, Spacio, Aura Lux Series (5 speeds, Sleep, Timer, LED Light)

> 📖 **Full Protocol & Command Reference:** See **[CODES.md](CODES.md)** for complete 32-bit NEC address and command byte provenance.

---

## Features

### 1. Multi-Transport Backend Options
You can configure each fan using any major IR blaster hardware:
* **Home Assistant Native Infrared (`infrared.*`):** Microsecond raw duration arrays (`RawIRCommand`).
* **ESPHome (`esphome.<device>_transmit_raw`):** Signed pulse/space timing arrays (+pulse, -space).
* **Broadlink Base64 (`remote.send_command`):** Native `0x26` packet format.
* **Tuya Base64 (`remote.send_command`):** Little-endian uint16 byte stream.
* **Pronto Hex:** Universal CCF format string.
* **Tasmota MQTT:** 32-bit NEC JSON payload.

### 2. Smart Switch Power Management & Resilient Boot-Gap Recovery
* **Auto Power-on with Boot Delay:** Turning on the fan will automatically switch on the physical smart plug first and wait **1.5s** for the MCU to boot before blasting IR.
* **Resilient Boot-Gap Recovery:** If an IR blaster is power-cycled, commands are cached with a **180s TTL** and automatically resynced once the blaster reconnects.
* **Physical Remote Precedence:** Signal decoding via native IR receiver immediately updates HA state and clears any pending resync queues.

---

## Installation

### Method 1: Using HACS (Recommended)
1. In Home Assistant, open **HACS** → **Integrations** → Click the three dots (⋮) in the top-right corner.
2. Select **Custom repositories**.
3. Under **URL**, add: `https://github.com/selvakk2k/superfan_ir`
4. Select **Integration** as the category and click **Add**.
5. Search for **Superfan IR**, click **Install**, and restart Home Assistant.

### Method 2: Manual Installation
1. Download this repository as a ZIP file.
2. Copy the folder `custom_components/superfan_ir` into your Home Assistant's `custom_components/` directory.
3. Restart Home Assistant.

---

## Configuration

1. In Home Assistant, navigate to **Settings → Devices & Services** → **+ Add Integration**.
2. Search for **Superfan IR Native**.
3. Fill in the initial configuration details:
   * **Name**: Friendly name for your fan.
   * **Fan Model**: Select the correct remote model mapping (T10 or T12/6).
   * **Backend**: Choose between `Native Infrared`, `ESPHome (Raw API Service)`, or `Legacy Remote (Tuya)`.
4. Choose the transmitting entity ID (the `infrared` emitter, the `remote` entity, or the ESPHome device name).
5. (Optional) After setup, click **Configure** (the cog) on the Integration card to bind a physical **Power Switch** to toggle the power line.

---

## ESPHome Configuration Examples

> ⚠️ **Note:** Pin numbers in the examples below (e.g., `P7`, `P26`, `GPIOXX`) are for demonstration purposes. Be sure to substitute them with the actual pin assignments for your specific hardware board.

### Option A: Modern Native Infrared (`ir_rf_proxy`) [Recommended]

Add this to your ESPHome device YAML:

```yaml
remote_receiver:
  id: ir_rx
  pin:
    number: P7 # Change to your IR receiver pin
    inverted: true
    mode: INPUT_PULLUP

remote_transmitter:
  id: ir_tx
  pin: P26 # Change to your IR transmitter pin
  carrier_duty_percent: 50%

# Exposes native infrared entities to Home Assistant
infrared:
  - platform: ir_rf_proxy
    name: IR Transmitter
    remote_transmitter_id: ir_tx
  - platform: ir_rf_proxy
    name: IR Receiver
    receiver_frequency: 38kHz
    remote_receiver_id: ir_rx
```

### Option B: Direct ESPHome Raw API Service

Add this to your ESPHome device YAML:

```yaml
api:
  services:
    - service: transmit_raw
      variables:
        command: int[]
      then:
        - remote_transmitter.transmit_raw:
            transmitter_id: tx
            carrier_frequency: 38kHz
            code: !lambda 'return command;'

remote_transmitter:
  pin: P26
  carrier_duty_percent: 50%
  id: tx
```

---

## Credits & License

Enhancements, custom raw timing conversions, and native `infrared` support developed by [@selvakk2k](https://github.com/selvakk2k) with design and ideation assistance from **Claude** (Anthropic) and code implementation assistance from **Gemini/Antigravity** (Google DeepMind).

Licensed under the **MIT License**. See the `LICENSE` file for details.
