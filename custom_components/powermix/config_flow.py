"""Config flow for Powermix."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (
    CONF_INCLUDED_SENSORS,
    CONF_MAIN_SENSOR,
    CONF_SENSOR_PREFIX,
    DEFAULT_SENSOR_PREFIX,
    DOMAIN,
    SENSOR_DOMAIN,
)

POWER_SELECTOR = selector.EntitySelector(
    selector.EntitySelectorConfig(
        domain=[SENSOR_DOMAIN],
        device_class=["power"],
    )
)


class PowermixConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the config flow for Powermix."""

    VERSION = 1

    def __init__(self) -> None:
        self._main_sensor: str | None = None

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if user_input is not None:
            self._main_sensor = user_input[CONF_MAIN_SENSOR]
            return await self.async_step_sensors()

        data_schema = vol.Schema({vol.Required(CONF_MAIN_SENSOR): POWER_SELECTOR})
        return self.async_show_form(step_id="user", data_schema=data_schema)

    async def async_step_sensors(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if not self._main_sensor:
            return await self.async_step_user()

        if user_input is not None:
            include = user_input.get(CONF_INCLUDED_SENSORS, []) or []
            prefix = user_input.get(CONF_SENSOR_PREFIX, DEFAULT_SENSOR_PREFIX)
            filtered = [entity for entity in include if entity != self._main_sensor]
            data = {
                CONF_MAIN_SENSOR: self._main_sensor,
                CONF_INCLUDED_SENSORS: filtered,
                CONF_SENSOR_PREFIX: prefix.strip() or DEFAULT_SENSOR_PREFIX,
            }
            friendly_title = await self._main_sensor_title()
            title = f"{friendly_title} breakdown"
            return self.async_create_entry(title=title, data=data)

        schema = vol.Schema(
            {
                vol.Optional(CONF_INCLUDED_SENSORS, default=[]): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain=[SENSOR_DOMAIN],
                        device_class=["power"],
                        multiple=True,
                        exclude_entities=[self._main_sensor],
                    )
                ),
                vol.Required(CONF_SENSOR_PREFIX, default=DEFAULT_SENSOR_PREFIX): str,
            }
        )
        return self.async_show_form(step_id="sensors", data_schema=schema)

    async def _main_sensor_title(self) -> str:
        if not self._main_sensor:
            return "Powermix"
        state = self.hass.states.get(self._main_sensor)
        if state:
            return state.attributes.get("friendly_name", self._main_sensor)
        return self._main_sensor


class PowermixOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        self._entry = entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        base = {**self._entry.data, **self._entry.options}
        main_sensor = base[CONF_MAIN_SENSOR]
        current_include = base.get(CONF_INCLUDED_SENSORS, [])
        current_prefix = base.get(CONF_SENSOR_PREFIX, DEFAULT_SENSOR_PREFIX)

        if user_input is not None:
            include = [entity for entity in user_input.get(CONF_INCLUDED_SENSORS, []) if entity != main_sensor]
            prefix = user_input.get(CONF_SENSOR_PREFIX, DEFAULT_SENSOR_PREFIX)
            data = {
                CONF_INCLUDED_SENSORS: include,
                CONF_SENSOR_PREFIX: prefix.strip() or DEFAULT_SENSOR_PREFIX,
            }
            return self.async_create_entry(title="", data=data)

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_INCLUDED_SENSORS, default=current_include
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain=[SENSOR_DOMAIN],
                        device_class=["power"],
                        multiple=True,
                        exclude_entities=[main_sensor],
                    )
                ),
                vol.Required(CONF_SENSOR_PREFIX, default=current_prefix): str,
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)


def async_get_options_flow(entry: config_entries.ConfigEntry) -> PowermixOptionsFlowHandler:
    return PowermixOptionsFlowHandler(entry)
