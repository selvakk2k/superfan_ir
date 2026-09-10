# Indian BLDC Fan Integration (formerly Superfan IR) (`superfan_ir`)

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=flat-square)](https://github.com/hacs/integration)
[![Stable](https://img.shields.io/github/v/release/selvakk2k/superfan_ir?label=Stable&style=flat-square)](https://github.com/selvakk2k/superfan_ir/releases/latest)
[![Beta](https://img.shields.io/github/v/release/selvakk2k/superfan_ir?include_prereleases&label=Beta&color=orange&style=flat-square)](https://github.com/selvakk2k/superfan_ir/releases)
[![AI-Assisted](https://img.shields.io/badge/AI%20Assisted-Antigravity%20%7C%20Claude-blueviolet?style=flat-square&logo=google)](https://github.com/selvakk2k)
[![AI Attribution](https://img.shields.io/badge/AI%20Attribution-AIA%20PAI%20Nc%20Hin-orange?style=flat-square)](https://aiattribution.github.io/interpret-attribution)

A Home Assistant custom integration for controlling Indian BLDC ceiling fans (Atomberg, Superfan, Orient, Activa, Goldmedal) via Infrared (IR) blasters. This integration provides native `fan` platform entities with accurate speed tiers, timer modes, smart power switch bindings, and multi-format blaster support.

> [!TIP]
> A companion Lovelace dashboard card is available: **[superfan-card](https://github.com/selvakk2k/superfan-card)** (Indian BLDC Fan Card).

---

## Table of Contents

1. [Key Features](#key-features)
2. [Supported Fan Brands & Remote Models](#supported-fan-brands--remote-models)
3. [IR Blaster Compatibility & Formats](#ir-blaster-compatibility--formats)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [ESPHome Blaster Configuration Examples](#esphome-blaster-configuration-examples)
7. [Troubleshooting & Logs](#troubleshooting--logs)
8. [My Integrations & Lovelace Cards](#my-integrations--lovelace-cards)
9. [Credits & License](#credits--license)

---

## Key Features

### 1. Multi-Format IR Dispatch
Transmit commands using any common smart IR blaster hardware without needing manual code learning:
* **Native Home Assistant Infrared (`ir_rf_proxy` - Recommended):** Uses Home Assistant's native `infrared` platform to send microsecond timing arrays directly to ESPHome or native transmitter entities.
* **ESPHome Raw Service:** Sends raw alternating pulse/space timings via native ESPHome API services (`esphome.<blaster>_transmit_raw`).
* **Broadlink:** Transmits base64 Pronto-encoded packets via Broadlink RM4/RM mini remotes.
* **Tuya Base64:** Sends compressed Tuya IR packets to Tuya-based Zigbee/Wi-Fi blasters (`remote.send_command`).
* **Tasmota / MQTT:** Dispatches raw or NEC hex strings over MQTT to Tasmota-flashed IR bridges.

### 2. Smart Switch Power Management
If your ceiling fan is connected through a physical smart switch or relay (e.g. Sonoff, Shelly, Tuya):
* **Auto Power-on with Boot Delay:** Turning on the fan or changing speeds automatically powers on the physical wall switch and waits for the fan's receiver microcontroller to initialize (configurable 1–3 seconds) before transmitting the IR payload.
* **Power-Off Bypass:** Turning the fan off cuts physical power immediately via the smart switch, saving standby power without relying on optical line-of-sight.

### 3. Symmetrical Diagnostics & Telemetry
Exposes last control source tracking and connection state sensors to monitor blaster responsiveness on your dashboard.

---

## Supported Fan Brands & Remote Models

During setup, select the remote model mapping matching your physical ceiling fan:

| Brand / Family | Remote Model | Speed Levels | Presets & Capabilities | Verified Hardware |
| :--- | :--- | :--- | :--- | :--- |
| **Atomberg** | Standard BLDC Remote | 6 Speeds (1–6 + Boost) | Boost Mode, Sleep Mode, Timer (1h, 2h, 3h, 6h), LED Toggle | ✅ Renesa, Efficio, Aris, Studio, Erica |
| **Superfan** | T10 Remote | 5 Speeds (1–5) | Breeze Mode, Speed Adjust, 2h Timer, 6h Timer | ✅ Super X, A, V, J, P, Visree T6/P6 |
| **Superfan** | T12/6 Remote | 3 Speeds (Low, Med, High) | Breeze Mode, Eco Mode, Sleep Mode, Reverse Mode, Wellness, AC Mix, 2h/6h Timer | ✅ Super Q Series |
| **Orient** | BLDC Remote | 5 Speeds (1–5 + Boost) | Breeze Mode, Sleep Mode, Boost Mode, Timer (2h, 4h, 6h, 8h) | ✅ I-Tome, Aeroslim, Wendy, Ecotech |
| **Activa** | BLDC Remote | 6 Speeds (1–6 + Boost) | Boost Mode, Sleep Mode, Timer (1h, 2h, 4h, 8h) | ✅ Gracia, Energia, Apsara |
| **Goldmedal** | BLDC Remote | 6 Speeds (1–6) | Sleep Mode, Breeze Mode, Timer (2h, 4h, 6h, 8h), LED Light | ✅ Opus Prime, Winzo, Spacio, Aura Lux |

---

## IR Blaster Compatibility & Formats

The integration supports automatic format detection and explicit format selection:

```
┌─────────────────────────────────────────────────────────────┐
│                    Home Assistant Fan Entity                │
└──────────────────────────────┬──────────────────────────────┘
                               │
            ┌──────────────────┴──────────────────┐
            ▼                                     ▼
   [Native HA Infrared]                   [Remote Services]
    • ir_rf_proxy (ESPHome)                • Broadlink Base64
    • ESPHome Raw Service                  • Tuya Base64
    • Tasmota / MQTT                       • Pronto Hex
```

---

## Installation

### Method 1: Using HACS (Recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=selvakk2k&repository=superfan_ir&category=integration)

1. Click the **Open repository in HACS** button above, or open **HACS** from your Home Assistant sidebar.
2. Click the top-right menu (⋮) → **Custom repositories** → Add `https://github.com/selvakk2k/superfan_ir` with category **Integration**.
3. Search for **Indian BLDC Fan IR**, click **Download**, and restart Home Assistant.

### Method 2: Manual Installation
1. Download the latest release ZIP from the [Releases](https://github.com/selvakk2k/superfan_ir/releases) page.
2. Copy the `custom_components/superfan_ir` folder into your Home Assistant `<config>/custom_components/` directory.
3. Restart Home Assistant.

---

## Configuration

1. In Home Assistant, go to **Settings → Devices & Services → Add Integration**.
2. Search for **Indian BLDC Fan IR**.
3. Fill in the setup wizard:
   * **Name**: Friendly name for your fan (e.g. *Living Room Fan*).
   * **Fan Model**: Select your brand and remote model (e.g. *Atomberg BLDC*, *Superfan T10*, *Orient BLDC*).
   * **IR Format**: Choose *Auto-Detect*, *Native Infrared*, *Broadlink*, *Tuya*, or *Tasmota*.
   * **Transmitter Entity**: Select the target transmitter entity or ESPHome device.
4. (Optional) After setup, click **Configure** on the integration card to bind a physical **Power Switch** entity.

---

## ESPHome Blaster Configuration Examples

For the best latency and reliability, use the native `ir_rf_proxy` component in ESPHome:

```yaml
remote_receiver:
  id: ir_rx
  pin:
    number: GPIO14
    inverted: true
    mode: INPUT_PULLUP

remote_transmitter:
  id: ir_tx
  pin: GPIO12
  carrier_duty_percent: 50%

# Exposes native infrared entities to Home Assistant
infrared:
  - platform: ir_rf_proxy
    name: "Living Room IR Transmitter"
    remote_transmitter_id: ir_tx
  - platform: ir_rf_proxy
    name: "Living Room IR Receiver"
    receiver_frequency: 38kHz
    remote_receiver_id: ir_rx
```

---

## Troubleshooting & Logs

### 1. Enabling Debug Logs

#### Via the UI (Dynamic, no restart required)
1. Go to **Settings → Devices & Services** → Select the **Indian BLDC Fan IR** card.
2. Click the top-right menu (**⋮**) → **Enable debug logging**.
3. Trigger commands from the dashboard, then click **Disable debug logging** to download the log file.

#### Via `configuration.yaml` (Persistent / Startup Issues)
To view detailed dispatch and decoding logs across Home Assistant restarts, add this to your `configuration.yaml` and restart Home Assistant:

```yaml
logger:
  default: warning
  logs:
    custom_components.superfan_ir: debug
```

### 2. IR Blaster Troubleshooting
* **Transmitter Line-of-Sight**: Verify your IR blaster LED has an unobstructed line of sight to the fan motor housing or canopy sensor dome.
* **Carrier Frequency**: Ensure your receiver/transmitter hardware is configured for **38 kHz** modulated carrier frequency.
* **Raw Protocol**: For ESPHome devices with native `infrared` components, select **Raw** or **Auto-Detect** in the integration configuration for microsecond-precise hardware pulsing.

---

## My Integrations & Lovelace Cards

| Integration / Card | Category | Description | Status |
| :--- | :--- | :--- | :--- |
| [Panasonic AC India](https://github.com/selvakk2k/ha-miraie-ac-in) | Integration | Local IR & Cloud MQTT control for Panasonic MirAIe Air Conditioners | `Stable` |
| [Panasonic AC India Card](https://github.com/selvakk2k/miraie-ac-card-in) | Lovelace Card | Modern Lovelace card for Panasonic ACs | `Stable` |
| [Indian BLDC Fan IR](https://github.com/selvakk2k/superfan_ir) | Integration | Native Home Assistant integration for Indian BLDC ceiling fans (Superfan, Atomberg) | `Stable` |
| [Indian BLDC Fan Card](https://github.com/selvakk2k/superfan-card) | Lovelace Card | Interactive Lovelace card with speed dial & mode toggles for BLDC fans | `Stable` |
| [IFB Washer Local](https://github.com/selvakk2k/ifb-washer-local) | Integration | Local Wi-Fi integration for IFB Front Load Washing Machines & Washer Dryers | `Beta` |
| [IFB Washer Card](https://github.com/selvakk2k/ifb-washer-card) | Lovelace Card | Dedicated Lovelace card for IFB washers & dryers with cycle controls | `Beta` |
| [Tinxy Local Python](https://github.com/selvakk2k/ha-tinxylocal) | Integration | Pure-Python local control for Tinxy smart switches and modules | `Stable` |
---

## Credits & License

### Project Contributors & AI Attribution
* **Lead Architecture & Hardware Validation**: [@selvakk2k](https://github.com/selvakk2k) — physical remote captures, protocol verification on hardware units, and domain architecture.
* **Code Implementation & Engineering**: **Antigravity** (Google DeepMind) — multi-brand protocol decoders, native `infrared` platform integration, and config flows.
* **Pre-Release Code Review & Auditing**: **Claude** (Anthropic) — independent code review, timing accuracy audits, and edge-case verification.

Licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.
