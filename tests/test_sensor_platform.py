from __future__ import annotations

from collections.abc import Callable
from typing import Any
from unittest.mock import patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.powermix.const import (
    CONF_INCLUDED_SENSORS,
    CONF_MAIN_SENSOR,
    CONF_PRODUCER_SENSORS,
    CONF_SENSOR_PREFIX,
    DEFAULT_SENSOR_PREFIX,
    DOMAIN,
)
from custom_components.powermix.sensor import (
    PowermixMirrorSensor,
    PowermixOtherSensor,
    async_setup_entry,
)
from tests.helpers import DummyHass


@pytest.fixture
def dummy_hass() -> DummyHass:
    return DummyHass()


@pytest.fixture(autouse=True)
def suppress_async_write_state():
    with patch(
        "custom_components.powermix.sensor.SensorEntity.async_write_ha_state", autospec=True
    ) as mocked:
        yield mocked


@pytest.mark.asyncio
async def test_async_setup_entry_adds_other_and_mirror_entities(dummy_hass: DummyHass) -> None:
    hass = dummy_hass
    entry = MockConfigEntry(domain=DOMAIN)
    config = {
        CONF_MAIN_SENSOR: "sensor.main",
        CONF_INCLUDED_SENSORS: ["sensor.ev", "sensor.ev"],  # duplicates are OK here
        CONF_PRODUCER_SENSORS: ["sensor.pv"],
        CONF_SENSOR_PREFIX: DEFAULT_SENSOR_PREFIX,
    }
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {"config": config}

    added: list[Any] = []

    def add_entities(entities: list[Any], update_before_add: bool = False) -> None:
        added.extend(entities)

    await async_setup_entry(hass, entry, add_entities)

    assert len(added) == 4  # 1 other sensor + 2 consumer mirrors + 1 producer mirror
    assert isinstance(added[0], PowermixOtherSensor)
    assert all(isinstance(entity, PowermixMirrorSensor) for entity in added[1:])
    roles = [entity.extra_state_attributes["sensor_role"] for entity in added[1:]]
    assert roles.count("consumer") == 2
    assert roles.count("producer") == 1


@pytest.mark.asyncio
async def test_other_sensor_refreshes_from_tracked_states(dummy_hass: DummyHass) -> None:
    hass = dummy_hass
    hass.states.set("sensor.main", "500", {"unit_of_measurement": "W"})
    hass.states.set("sensor.heat_pump", "150", {})
    hass.states.set("sensor.ev", "100", {})

    tracker: dict[str, Any] = {}

    def fake_track_state_change(
        hass_obj: DummyHass, entities: list[str], action: Callable[[Any], None]
    ) -> Callable[[], None]:
        tracker["entities"] = entities
        tracker["action"] = action
        return lambda: tracker.update({"unsubscribed": True})

    sensor = PowermixOtherSensor(
        "entry123",
        "Powermix",
        "sensor.main",
        ["sensor.heat_pump", "sensor.ev", "sensor.main"],
        ["sensor.pv"],
    )
    sensor.hass = hass

    with patch(
        "custom_components.powermix.sensor.async_track_state_change_event",
        side_effect=fake_track_state_change,
    ):
        await sensor.async_added_to_hass()

    assert sensor.native_value == 250.0
    # Only unique sensors without the main sensor are kept
    assert sensor.extra_state_attributes["included_sensors"] == [
        "sensor.heat_pump",
        "sensor.ev",
    ]
    assert sensor.extra_state_attributes["producer_sensors"] == ["sensor.pv"]
    assert sensor.native_unit_of_measurement == "W"
    assert tracker["entities"] == ["sensor.main", "sensor.heat_pump", "sensor.ev"]

    hass.states.set("sensor.ev", "200", {})
    tracker["action"](None)
    assert sensor.native_value == 150.0


@pytest.mark.asyncio
async def test_mirror_sensor_tracks_source_and_updates_name(dummy_hass: DummyHass) -> None:
    hass = dummy_hass
    hass.states.set(
        "sensor.server_rack",
        "450",
        {
            "unit_of_measurement": "W",
            "friendly_name": "Server Rack",
        },
    )

    recorded: dict[str, Any] = {}

    def fake_track(hass_obj: DummyHass, entities: list[str], action: Callable[[Any], None]):
        recorded["entities"] = entities
        recorded["action"] = action
        return lambda: None

    sensor = PowermixMirrorSensor(
        "entry123", "Powermix", "sensor.server_rack", role="consumer"
    )
    sensor.hass = hass

    with patch(
        "custom_components.powermix.sensor.async_track_state_change_event", side_effect=fake_track
    ):
        await sensor.async_added_to_hass()

    assert sensor.native_value == 450.0
    assert sensor.native_unit_of_measurement == "W"
    assert sensor.name == "Powermix Server Rack"
    assert recorded["entities"] == ["sensor.server_rack"]
    assert sensor.extra_state_attributes["sensor_role"] == "consumer"

    hass.states.remove("sensor.server_rack")
    recorded["action"](None)
    assert sensor.native_value is None
    # Name stays at last friendly name even if the source disappears.
    assert sensor.name == "Powermix Server Rack"


@pytest.mark.asyncio
async def test_other_sensor_allows_negative_only_when_producers_present(dummy_hass: DummyHass) -> None:
    hass = dummy_hass
    hass.states.set("sensor.main", "100", {"unit_of_measurement": "W"})
    hass.states.set("sensor.consumer", "150", {})

    sensor_no_prod = PowermixOtherSensor(
        "entry1",
        "Powermix",
        "sensor.main",
        ["sensor.consumer"],
        [],
    )
    sensor_no_prod.hass = hass
    sensor_no_prod._refresh_state()  # type: ignore[attr-defined]
    assert sensor_no_prod.native_value == 0.0

    sensor_with_prod = PowermixOtherSensor(
        "entry2",
        "Powermix",
        "sensor.main",
        ["sensor.consumer"],
        ["sensor.pv"],
    )
    sensor_with_prod.hass = hass
    sensor_with_prod._refresh_state()  # type: ignore[attr-defined]
    assert sensor_with_prod.native_value == -50.0
