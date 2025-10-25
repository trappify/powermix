# Configuration

1. Install the `powermix` custom integration via HACS (Custom repository) or copy the
   `custom_components/powermix` directory into your Home Assistant `config/custom_components` folder.
2. Restart Home Assistant and add **Powermix** from *Settings → Devices & Services*.
3. Pick the **main power sensor** (typically your total household consumption sensor).
4. Choose the **sensors to subtract**. Powermix mirrors each selection with the configured prefix and subtracts their values from the main power sensor to derive the *Other Usage* sensor.
5. Set the **prefix** you want Powermix to apply to every created sensor. This makes it easy to locate them in Grafana or any downstream database.

After saving the flow you will get:
- `<prefix> Other Usage`: `main - sum(selected)` clamped at zero.
- `<prefix> <Friendly Name>` for every selected sensor—these mirror the original values so downstream tools can filter on the prefix.

Use the integration's Options flow to update the included sensors or change the prefix later without re-adding the entry.
