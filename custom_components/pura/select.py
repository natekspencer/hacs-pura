"""Support for Pura fragrance slots."""
from __future__ import annotations

from datetime import timedelta
import functools

from pypura import PuraApiException, fragrance_name
import voluptuous as vol

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity_platform import (
    AddEntitiesCallback,
    async_get_current_platform,
)

from .const import ATTR_DURATION, ATTR_INTENSITY, ATTR_SLOT, DOMAIN, ERROR_AWAY_MODE
from .entity import PuraDataUpdateCoordinator, PuraEntity

SELECT_DESCRIPTION = SelectEntityDescription(key="fragrance", name="Fragrance")

SERVICE_START_TIMER = "start_timer"
SERVICE_TIMER_SCHEMA = vol.All(
    cv.make_entity_service_schema(
        {
            vol.Optional(ATTR_SLOT): vol.All(vol.Coerce(int), vol.Range(min=1, max=2)),
            vol.Required(ATTR_INTENSITY): vol.All(
                vol.Coerce(int), vol.Range(min=1, max=10)
            ),
            vol.Required(ATTR_DURATION): cv.positive_time_period,
        },
    )
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Pura selects using config entry."""
    coordinator: PuraDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = [
        PuraSelectEntity(
            coordinator=coordinator,
            config_entry=config_entry,
            description=SELECT_DESCRIPTION,
            device_id=device["device_id"],
        )
        for device_type, devices in coordinator.devices.items()
        if device_type == "wall"
        for device in devices
    ]

    if not entities:
        return

    async_add_entities(entities)

    platform = async_get_current_platform()
    platform.async_register_entity_service(
        SERVICE_START_TIMER, SERVICE_TIMER_SCHEMA, "async_start_timer"
    )


class PuraSelectEntity(PuraEntity, SelectEntity):
    """Pura select."""

    @property
    def current_option(self) -> str:
        """Return the selected entity option to represent the entity state."""
        device = self.get_device()
        if device["bay_1"]["active_at"]:
            return self.options[1]
        if device["bay_2"]["active_at"]:
            return self.options[2]
        return "Off"

    @property
    def options(self) -> list[str]:
        """Return a set of selectable options."""
        dev = self.get_device()
        opts = [f"Slot {i}: {fragrance_name(dev[f'bay_{i}']['code'])}" for i in (1, 2)]
        return ["Off"] + opts

    @property
    def icon(self) -> str:
        """Return the icon to use in the frontend."""
        return f"mdi:scent{'-off' if self.current_option=='Off' else ''}"

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        if option == "Off":
            job = functools.partial(self.coordinator.api.stop_all, self._device_id)
        elif self.get_device()["controller"] == "away":
            raise PuraApiException(ERROR_AWAY_MODE)
        else:
            bay = self.options.index(option)
            job = functools.partial(
                self.coordinator.api.set_always_on, self._device_id, bay=bay
            )

        if await self.hass.async_add_executor_job(job):
            await self.coordinator.async_request_refresh()

    async def async_start_timer(
        self, *, slot: int | None = None, intensity: int, duration: timedelta
    ) -> None:
        """Start a fragrance timer."""
        if not slot:
            device = self.get_device()
            runtime = "wearing_time"
            slot = 1 if device["bay_1"][runtime] <= device["bay_2"][runtime] else 2

        if await self.hass.async_add_executor_job(
            functools.partial(
                self.coordinator.api.set_timer,
                self._device_id,
                bay=slot,
                intensity=intensity,
                end=duration,
            )
        ):
            await self.coordinator.async_request_refresh()
