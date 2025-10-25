"""Sensor platform for Powermix."""

from __future__ import annotations

from collections.abc import Iterable

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, State, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .lib import calculate_other, coerce_float

from .const import (
    CONF_INCLUDED_SENSORS,
    CONF_MAIN_SENSOR,
    CONF_PRODUCER_SENSORS,
    CONF_SENSOR_PREFIX,
    DEFAULT_SENSOR_PREFIX,
    DOMAIN,
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    entry_data = hass.data[DOMAIN][entry.entry_id]["config"]
    main_sensor: str = entry_data[CONF_MAIN_SENSOR]
    selected: list[str] = [
        sensor for sensor in entry_data.get(CONF_INCLUDED_SENSORS, []) if sensor != main_sensor
    ]
    producers: list[str] = [
        sensor for sensor in entry_data.get(CONF_PRODUCER_SENSORS, []) if sensor != main_sensor
    ]
    prefix: str = entry_data.get(CONF_SENSOR_PREFIX, DEFAULT_SENSOR_PREFIX)

    entities: list[SensorEntity] = [
        PowermixOtherSensor(entry.entry_id, prefix, main_sensor, selected, producers)
    ]

    entities.extend(
        PowermixMirrorSensor(entry.entry_id, prefix, source, role="consumer")
        for source in selected
    )

    entities.extend(
        PowermixMirrorSensor(entry.entry_id, prefix, source, role="producer")
        for source in producers
    )

    async_add_entities(entities)


class PowermixBaseSensor(SensorEntity):
    """Common helpers for Powermix entities."""

    _attr_should_poll = False

    def __init__(self) -> None:
        self._unsubscribe: CALLBACK_TYPE | None = None

    async def async_will_remove_from_hass(self) -> None:
        if self._unsubscribe:
            self._unsubscribe()
            self._unsubscribe = None


class PowermixOtherSensor(PowermixBaseSensor):
    """Sensor that exposes (main - selected) power usage."""

    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        entry_id: str,
        prefix: str,
        main_sensor: str,
        selected: Iterable[str],
        producers: Iterable[str],
    ) -> None:
        super().__init__()
        self._main_sensor = main_sensor
        self._selected = list(dict.fromkeys(s for s in selected if s != main_sensor))
        self._producers = list(dict.fromkeys(s for s in producers if s != main_sensor))
        self._allow_negative = bool(self._producers)
        self._attr_name = f"{prefix} Other Usage"
        self._attr_unique_id = f"{entry_id}_other"
        self._native_value: float | None = None
        self._attr_native_unit_of_measurement: str | None = None
        self._attr_extra_state_attributes = {
            "main_sensor": self._main_sensor,
            "included_sensors": self._selected,
            "producer_sensors": self._producers,
        }

    @property
    def native_value(self) -> float | None:
        return self._native_value

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._refresh_state()
        self.async_write_ha_state()
        self._unsubscribe = async_track_state_change_event(
            self.hass,
            [self._main_sensor, *self._selected],
            self._handle_state_change,
        )

    @callback
    def _handle_state_change(self, _: Event | None) -> None:
        self._refresh_state()
        self.async_write_ha_state()

    def _refresh_state(self) -> None:
        main_state = self._get_state(self._main_sensor)
        selected_states = [self._get_state(entity) for entity in self._selected]
        main_value, unit = _value_in_watts(main_state)
        part_values = []
        for state in selected_states:
            value, _ = _value_in_watts(state)
            part_values.append(value)
        self._native_value = calculate_other(
            main_value,
            part_values,
            allow_negative=self._allow_negative,
        )
        self._attr_native_unit_of_measurement = unit

    def _get_state(self, entity_id: str) -> State | None:
        return self.hass.states.get(entity_id)


class PowermixMirrorSensor(PowermixBaseSensor):
    """Clone of a source power sensor prefixed for easier discovery."""

    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self, entry_id: str, prefix: str, source_entity_id: str, *, role: str
    ) -> None:
        super().__init__()
        self._source_entity_id = source_entity_id
        self._prefix = prefix
        self._role = role
        slug = _slugify(source_entity_id)
        self._attr_unique_id = f"{entry_id}_mirror_{slug}"
        self._attr_name = f"{prefix} {source_entity_id}"
        self._native_value: float | None = None
        self._attr_native_unit_of_measurement: str | None = None
        self._attr_extra_state_attributes = {
            "source_entity_id": self._source_entity_id,
            "sensor_role": self._role,
        }

    @property
    def native_value(self) -> float | None:
        return self._native_value

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._sync_from_source()
        self.async_write_ha_state()
        self._unsubscribe = async_track_state_change_event(
            self.hass,
            [self._source_entity_id],
            self._handle_state_change,
        )

    @callback
    def _handle_state_change(self, _: Event | None) -> None:
        self._sync_from_source()
        self.async_write_ha_state()

    def _sync_from_source(self) -> None:
        state = self.hass.states.get(self._source_entity_id)
        friendly_name = None
        if state:
            value, unit = _value_in_watts(state)
            self._native_value = value
            self._attr_native_unit_of_measurement = unit
            friendly_name = state.attributes.get("friendly_name")
        else:
            self._native_value = None
        if friendly_name:
            self._attr_name = f"{self._prefix} {friendly_name}"

    async def async_will_remove_from_hass(self) -> None:
        await super().async_will_remove_from_hass()


def _slugify(value: str) -> str:
    return value.lower().replace(".", "_").replace(" ", "_")


def _value_in_watts(state: State | None) -> tuple[float | None, str | None]:
    if not state:
        return None, None
    value = coerce_float(state.state)
    unit_attr = state.attributes.get("unit_of_measurement")
    normalized = _normalize_unit(unit_attr)
    if value is None:
        return None, _unit_label(normalized, unit_attr)
    if normalized == "kW":
        return value * 1000.0, "W"
    if normalized == "W":
        return value, "W"
    return value, unit_attr


def _normalize_unit(unit: str | None) -> str | None:
    if not unit:
        return None
    text = str(unit).strip().lower()
    if text in {"kw", "kilowatt", "kilowatts"}:
        return "kW"
    if text in {"w", "watt", "watts"}:
        return "W"
    return None


def _unit_label(normalized: str | None, original: str | None) -> str | None:
    if normalized == "W":
        return "W"
    if normalized == "kW":
        return "W"
    return original
