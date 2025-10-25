# Powermix

Home Assistant custom integration that mirrors selected power sensors (e.g. EV charger, heat pump, server rack) with a shared prefix so dashboards can discover them easily. It also exposes a `<prefix> Other Usage` entity that subtracts your chosen consumers from the main household power sensor, optionally allowing negative values when you configure producer sensors (PV, batteries) to highlight export periods.

## Requirements
- Home Assistant 2024.5 or newer
- Existing power sensors (`device_class: power`)

## Installation
1. Add this repository to HACS (Custom repositories → Integration).
2. Install **Powermix** and restart Home Assistant.
3. Add the integration via *Settings → Devices & Services → Add Integration*.

## Configuration
1. Pick the **main power sensor** (typically total consumption / grid meter).
2. Select the **consumer sensors** you want mirrored and subtracted.
3. (Optional) Select **producer sensors** (PV/battery) so “Other Usage” can go negative during export.
4. Set a **prefix** to group all Powermix entities (default `Powermix`).

You can revisit the configuration later via the integration’s **Reconfigure** dialog to tweak sensors or the prefix. See `docs/configuration.md` for more details, or spin up the included dev environment (`./scripts/ha up -d`) to experiment safely.***
