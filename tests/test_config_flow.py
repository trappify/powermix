from __future__ import annotations

import pytest
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.powermix.config_flow import (
    PowermixConfigFlow,
    PowermixOptionsFlowHandler,
)
from custom_components.powermix.const import (
    CONF_INCLUDED_SENSORS,
    CONF_MAIN_SENSOR,
    CONF_PRODUCER_SENSORS,
    CONF_SENSOR_PREFIX,
    DEFAULT_SENSOR_PREFIX,
    DOMAIN,
)
from tests.helpers import DummyHass


@pytest.mark.asyncio
async def test_config_flow_filters_main_sensor_and_uses_friendly_title() -> None:
    hass = DummyHass()
    hass.states.set(
        "sensor.total_power",
        "500",
        {
            "friendly_name": "Whole Home",
        },
    )

    flow = PowermixConfigFlow()
    flow.hass = hass

    # Step 1: user picks the main sensor
    first = await flow.async_step_user({CONF_MAIN_SENSOR: "sensor.total_power"})
    assert first["type"] == FlowResultType.FORM

    # Step 2: user selects breakdown sensors and a blank prefix
    result = await flow.async_step_sensors(
        {
            CONF_INCLUDED_SENSORS: [
                "sensor.ev",
                "sensor.total_power",  # should be stripped
                "sensor.ev",
            ],
            CONF_PRODUCER_SENSORS: [
                "sensor.pv",
                "sensor.total_power",
            ],
            CONF_SENSOR_PREFIX: "   ",
        }
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "Whole Home breakdown"
    data = result["data"]
    assert data[CONF_MAIN_SENSOR] == "sensor.total_power"
    # Duplicates preserved, but the main sensor is filtered out.
    assert data[CONF_INCLUDED_SENSORS] == ["sensor.ev", "sensor.ev"]
    assert data[CONF_PRODUCER_SENSORS] == ["sensor.pv"]
    assert data[CONF_SENSOR_PREFIX] == DEFAULT_SENSOR_PREFIX


@pytest.mark.asyncio
async def test_options_flow_updates_include_and_prefix() -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_MAIN_SENSOR: "sensor.total_power",
            CONF_INCLUDED_SENSORS: ["sensor.ev"],
            CONF_PRODUCER_SENSORS: ["sensor.pv"],
            CONF_SENSOR_PREFIX: "Powermix",
        },
    )

    flow = PowermixOptionsFlowHandler(entry)
    form = await flow.async_step_init()
    assert form["type"] == FlowResultType.FORM

    result = await flow.async_step_init(
        {
            CONF_INCLUDED_SENSORS: [
                "sensor.ev",
                "sensor.heat_pump",
                "sensor.total_power",
            ],
            CONF_PRODUCER_SENSORS: [
                "sensor.pv",
                "sensor.battery",
                "sensor.total_power",
            ],
            CONF_SENSOR_PREFIX: " Custom Prefix ",
        }
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    options = result["data"]
    assert options[CONF_INCLUDED_SENSORS] == ["sensor.ev", "sensor.heat_pump"]
    assert options[CONF_PRODUCER_SENSORS] == ["sensor.pv", "sensor.battery"]
    assert options[CONF_SENSOR_PREFIX] == "Custom Prefix"
