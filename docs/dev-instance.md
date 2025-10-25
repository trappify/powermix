# Home Assistant dev instance

A minimal HA environment ships with the repo so you can exercise the Powermix integration without touching your live installation.

## Requirements
- Docker + Docker Compose Plugin

## Start the stack
```bash
HA_PORT=8124 ./scripts/ha up -d
```

(set the `HA_PORT` env var to whichever free port you prefer; defaults to `8124` to avoid clashing with any local Home Assistant installs). The stack hosts Home Assistant at `http://localhost:${HA_PORT:-8124}` with its config stored under `ha_dev/config`. The `custom_components` directory from this repo is bind-mounted into the container, so edits to the integration are immediately available after a Home Assistant restart.

To tail logs or stop the stack:
```bash
./scripts/ha logs
./scripts/ha down
./scripts/ha reset   # optional: stop HA, wipe /ha_dev/config, and reapply the template
```

## Initial setup steps inside Home Assistant
1. Log in with the pre-created owner account `powermix` / `powermix` (no onboarding wizard will appear; the steps are already marked as done).
2. Visit **Settings → Devices & Services → Add Integration** and pick **Powermix**.
3. Select `sensor.total_power` as the main sensor, then select any combination of `sensor.heat_pump`, `sensor.ev_charger`, or `sensor.server_rack` for the breakdown list.
4. Accept the default prefix (or provide your own) to create the prefixed mirror sensors plus the “Other Usage” entity.

### Simulating power loads
Use the helpers under **Settings → Devices & Services → Helpers** (or the Lovelace sliders) to adjust:
- `input_number.main_power`
- `input_number.heat_pump_power`
- `input_number.ev_charger_power`
- `input_number.server_rack_power`

Each slider feeds a template sensor with `device_class: power`, giving you realistic inputs to test the Powermix flow. Tweaking the sliders updates Home Assistant state instantly, so you can watch the Powermix sensors respond in real time.

## Resetting the dev environment
Run `./scripts/ha reset` to stop the stack (if running), wipe `ha_dev/config`, and reapply the template. The next `./scripts/ha up -d` call will boot a clean instance with the same default helpers and credentials.
