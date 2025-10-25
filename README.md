# Powermix

Home Assistant custom integration that mirrors selected power sensors and creates an "other" sensor showing the remainder of a main power feed. Use it to build Grafana dashboards with a consistent set of prefixed sensors while keeping the heavy calculations inside Home Assistant before the data hits InfluxDB.

## HACS installation

Powermix ships as a HACS-compatible custom integration. Add `https://github.com/trappify/powermix` to **HACS → Integrations → Custom repositories**, install **Powermix**, restart Home Assistant, and add the integration via *Settings → Devices & Services*. See `docs/configuration.md` for a walkthrough of the setup flow (main sensor, consumer sensors, optional producer sensors, and the shared prefix).

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
./scripts/test
```

## Home Assistant dev instance

Use the bundled Docker setup to spin up a Home Assistant playground with the Powermix integration already mounted:

```bash
HA_PORT=8124 ./scripts/ha up -d   # start HA on http://localhost:8124 (override HA_PORT as needed)
./scripts/ha logs                 # follow container logs
./scripts/ha down                 # stop the stack
./scripts/ha reset                # wipe the runtime config and re-seed from the template
```

The dev instance already ships with an owner account (`powermix` / `powermix`) and onboarding disabled, so you land straight on the login screen. Once inside, adjust the provided `input_number` helpers (Total Power, Heat Pump, EV Charger, Server Rack) to simulate power usage, then add the Powermix integration via *Settings → Devices & Services*. More details live in `docs/dev-instance.md`.
