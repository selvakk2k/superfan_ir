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

---

## Features

### 1. Dual Dispatch Backend Options
You can configure each fan using one of two IR transmission methods:
* **Native Infrared (Recommended):** Converts the legacy Tuya Base64 payloads into raw microsecond timings on-the-fly, allowing direct compatibility with Home Assistant's native `infrared` platform using `RawIRCommand` structures.
* **Legacy Remote (Tuya Only):** Passes the Tuya base64 strings directly to any configured Tuya-compatible `remote` entity (such as a Tuya-based local smart IR blaster) via the `remote.send_command` service.

### 2. Smart Switch Power Management
If your fan is connected to a smart wall switch or plug (e.g. Sonoff, Shelly, Tuya), you can bind it directly within the integration options:
* **Auto Power-on with Boot Delay:** Turning on the fan or adjusting the speed will automatically switch on the physical smart plug first and wait **2 seconds** for the fan's receiver board to boot before blasting the IR command.
* **Power-Off Bypass:** Turning the fan off in Home Assistant will skip sending the IR command entirely and cleanly cut physical power via the smart switch, instantly updating the UI to "Off".

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
   * **Backend**: Choose either `Native Infrared` or `Legacy Remote (Tuya)`.
4. Choose the transmitting entity ID (the `infrared` emitter or the `remote` entity).
5. (Optional) After setup, click **Configure** (the cog) on the Integration card to bind a physical **Power Switch** to toggle the power line.

---

## Credits & License

Enhancements, custom raw timing conversions, and native `infrared` support developed by [@selvakk2k](https://github.com/selvakk2k) with design and ideation assistance from **Claude** (Anthropic) and code implementation assistance from **Gemini/Antigravity** (Google DeepMind).

Licensed under the **MIT License**. See the `LICENSE` file for details.
