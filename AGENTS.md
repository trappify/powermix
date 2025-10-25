# AGENTS

## Purpose
- Mirror one or more existing Home Assistant power sensors with a prefixed name so they are easy to find in Grafana or other dashboards.
- Expose a computed "other usage" sensor that subtracts the selected consumers from a main whole-home power sensor.

## Components
- `powermix.calculator`: Pure helpers that sum sensors and compute remainder, shared between the integration and tests.
- `custom_components/powermix`: Home Assistant integration with config flow, entity setup, and sensor platform.
- `tests/`: Pytest suite that exercises the calculator helpers and the entity logic without spinning up a full Home Assistant core.

## Operational Notes
- All sensors produced by the integration share a configurable prefix so downstream tooling can filter on it.
- The integration listens to state changes for the selected sensors and recomputes values immediately; there is no polling interval.
- Selected sensors must be normal Home Assistant `sensor` entities with power readings (Watts). Empty/unknown source states are treated as zero for the mirrored entities and excluded from the "other" calculation.

## Testing
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
pytest
```
