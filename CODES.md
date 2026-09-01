# Infrared Protocol & Code Provenance Reference

This document details the 32-bit NEC infrared carrier protocols, address byte configurations, and command byte maps for all supported Indian-market BLDC ceiling fans in the `superfan_ir` integration.

---

## 1. Protocol Architecture & Carrier Specification

All supported models utilize the **38kHz NEC Infrared Protocol** (LSB-first):
* **Header**: `9000µs` pulse + `4500µs` space
* **Logical 0**: `560µs` pulse + `560µs` space
* **Logical 1**: `560µs` pulse + `1690µs` space
* **Stop Bit**: `560µs` pulse
* **Structure**: 16-bit Address (`Addr_Low`, `Addr_High`) + 8-bit Command (`Cmd`) + 8-bit Inverted Command (`~Cmd`)

$$\text{32-bit NEC Frame} = [\text{Address (16-bit)}] + [\text{Command (8-bit)}] + [\text{Command Inverted (8-bit)}]$$

---

## 2. Supported Brands, Addresses & Verification Status

| Brand / Model Identifier | 16-Bit Address | Capture / Verification Provenance | Status |
| :--- | :--- | :--- | :--- |
| **Superfan (T10 Series)** | `0x00DF` | Physical Remote Logic Analyzer & TSOP38238 Capture | ✅ Hardware Verified |
| **Superfan (T12/6 Series)** | `0x00DF` | Physical Remote Logic Analyzer & TSOP38238 Capture | ✅ Hardware Verified |
| **Atomberg (Renesa, Efficio, Studio, Aris)** | `0xF300` | Physical Remote Hardware Capture | ✅ Hardware Verified |
| **Activa (Gracia, Energia, Apsara Series)** | `0x5AA5` | App-Sourced Database Cross-Checked against NEC Specs | ✅ Verified |
| **Orient Electric (I-Tome, Aeroslim, Wendy)** | `0x6B94` | App-Sourced Database Cross-Checked against NEC Specs | ✅ Verified |
| **Goldmedal (Opus Prime, Winzo, Spacio)** | `0x5A95` | App-Sourced Database Cross-Checked against NEC Specs | ✅ Verified |

---

## 3. Command Byte Tables (Hex)

### Superfan (T10 & T12/6) — Address `0x00DF`
| Action / Speed | Command Byte | NEC 32-bit Hex Code |
| :--- | :--- | :--- |
| **Power Toggle** | `0x98` | `0x00DF9867` |
| **Speed 1 / Low / Eco / Sleep** | `0x94` | `0x00DF946B` |
| **Speed 2** | `0x99` | `0x00DF9966` |
| **Speed 3 / Medium** | `0x95` | `0x00DF956A` |
| **Speed 4** | `0x9A` | `0x00DF9A65` |
| **Speed 5 / High** | `0x96` | `0x00DF9669` |
| **Breeze Mode** | `0x9C` | `0x00DF9C63` |
| **2-Hour Timer** | `0x9F` | `0x00DF9F60` |
| **6-Hour Timer** | `0x9E` | `0x00DF9E61` |
| **Reverse Direction** | `0x91` | `0x00DF916E` |
| **Wellness Mode** | `0x92` | `0x00DF926D` |
| **AC Mix** | `0x97` | `0x00DF9768` |

### Atomberg (Renesa, Efficio, Studio) — Address `0xF300`
| Action / Speed | Command Byte | NEC 32-bit Hex Code |
| :--- | :--- | :--- |
| **Power Toggle** | `0x03` | `0xF30003FC` |
| **Speed 1** | `0x04` | `0xF30004FB` |
| **Speed 2** | `0x05` | `0xF30005FA` |
| **Speed 3** | `0x06` | `0xF30006F9` |
| **Speed 4** | `0x07` | `0xF30007F8` |
| **Speed 5** | `0x08` | `0xF30008F7` |
| **Boost / Speed 6** | `0x09` | `0xF30009F6` |
| **Sleep Mode** | `0x0A` | `0xF3000AF5` |
| **Timer** | `0x0B` | `0xF3000BF4` |
| **LED Light** | `0x0C` | `0xF3000CF3` |

### Activa (Gracia / Energia) — Address `0x5AA5`
| Action / Speed | Command Byte | NEC 32-bit Hex Code |
| :--- | :--- | :--- |
| **Power Toggle** | `0x01` | `0x5AA501FE` |
| **Speed 1..6** | `0x02` .. `0x07` | `0x5AA502FD` .. `0x5AA507F8` |
| **Nature Mode** | `0x08` | `0x5AA508F7` |
| **Smart Mode** | `0x09` | `0x5AA509F6` |
| **LED Light** | `0x0A` | `0x5AA50AF5` |
| **Timer 2h / 4h / 8h** | `0x0C` / `0x0D` / `0x0E` | `0x5AA50CF3` / `0x5AA50DF2` / `0x5AA50EF1` |
| **Reverse** | `0x0F` | `0x5AA50FF0` |

### Orient Electric (I-Tome / Aeroslim) — Address `0x6B94`
| Action / Speed | Command Byte | NEC 32-bit Hex Code |
| :--- | :--- | :--- |
| **Power On** | `0x01` | `0x6B9401FE` |
| **Power Off** | `0x02` | `0x6B9402FD` |
| **Speed 1..5** | `0x03` .. `0x07` | `0x6B9403FC` .. `0x6B9407F8` |
| **Timer 2h / 4h / 6h** | `0x08` / `0x09` / `0x0A` | `0x6B9408F7` / `0x6B9409F6` / `0x6B940AF5` |
| **LED Light** | `0x0B` | `0x6B940BF4` |

### Goldmedal (Opus / Winzo) — Address `0x5A95`
| Action / Speed | Command Byte | NEC 32-bit Hex Code |
| :--- | :--- | :--- |
| **Power Toggle** | `0x01` | `0x5A9501FE` |
| **Speed 1..5** | `0x02` .. `0x06` | `0x5A9502FD` .. `0x5A9506F9` |
| **Sleep Mode** | `0x07` | `0x5A9507F8` |
| **Timer 1h / 2h / 3h / 6h**| `0x08` / `0x09` / `0x0A` / `0x0B` | `0x5A9508F7` .. `0x5A950BF4` |
| **LED Light** | `0x0C` | `0x5A950CF3` |

---

## 4. Multi-Transport Output Formats Generated

* **Home Assistant Native Infrared (`infrared.*`)**: Microsecond duration pulse/space integers.
* **ESPHome (`remote_transmitter.transmit_raw`)**: Microsecond timing array with negative spaces (`[+9000, -4500, +560, -560, ...]`).
* **Broadlink Base64 (`remote.send_command`)**: `0x26` packet format encoded in Base64 (`b64:Jg...`).
* **Tuya Base64 (`remote.send_command`)**: Little-endian 16-bit integer pulse timings in Base64.
* **Pronto Hex**: Universal CCF format string (`0000 006D 0022 0000 ...`).
* **Tasmota MQTT**: JSON payload `{"Protocol": "NEC", "Bits": 32, "Data": "0x00DF9867"}`.
