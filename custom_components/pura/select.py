"""Support for Pura fragrance slots."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta
import functools

from pypura import PuraApiException
import voluptuous as vol

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity_platform import (
    AddEntitiesCallback,
    async_get_current_platform,
)

from . import PuraConfigEntry
from .const import ATTR_DURATION, ATTR_INTENSITY, ATTR_SLOT, ERROR_AWAY_MODE
from .coordinator import PuraDataUpdateCoordinator
from .entity import PuraEntity, has_fragrance
from .helpers import get_device_id

INTENSITY_MAP = {"subtle": 3, "medium": 6, "strong": 10}

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
    hass: HomeAssistant, entry: PuraConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Pura selects using config entry."""
    coordinator: PuraDataUpdateCoordinator = entry.runtime_data

    entities = [
        PuraSelectEntity(
            coordinator=coordinator,
            description=descriptor,
            device_type=device_type,
            device_id=get_device_id(device),
        )
        for device_type, devices in coordinator.devices.items()
        if device_type == "wall"
        for device in devices
        for descriptor in SELECT_DESCRIPTIONS
    ]

    if not entities:
        return

    async_add_entities(entities)

    platform = async_get_current_platform()
    platform.async_register_entity_service(
        SERVICE_START_TIMER, SERVICE_TIMER_SCHEMA, "async_start_timer"
    )


@dataclass(kw_only=True)
class PuraSelectEntityDescription(SelectEntityDescription):
    """Pura select entity description."""

    current_fn: Callable[[dict], str]
    options_fn: Callable[[dict], list[str]] | None = None
    select_fn: Callable[[PuraSelectEntity, str], functools.partial[bool]]


SELECT_DESCRIPTIONS = (
    PuraSelectEntityDescription(
        key="fragrance",
        translation_key="fragrance",
        current_fn=lambda data: "off" if (b := data["bay"]) == 0 else f"slot_{b}",
        options_fn=lambda data: ["off"]
        + [f"slot_{i}" for i in (1, 2) if has_fragrance(data, i)],
        select_fn=lambda select, option: functools.partial(
            select.coordinator.api.set_always_on,
            select._device_id,
            bay=int(option.replace("slot_", "")),
        ),
    ),
    PuraSelectEntityDescription(
        key="intensity",
        translation_key="intensity",
        entity_category=EntityCategory.CONFIG,
        current_fn=lambda data: data["intensity"] or "off",
        options=["off", "subtle", "medium", "strong"],
        select_fn=lambda select, option: functools.partial(
            select.coordinator.api.set_intensity,
            select._device_id,
            bay=select._intensity_data["bay"],
            controller=select._intensity_data["controller"],
            intensity=INTENSITY_MAP[option],
        ),
    ),
)


class PuraSelectEntity(PuraEntity, SelectEntity):
    """Pura select."""

    entity_description: PuraSelectEntityDescription

    @property
    def current_option(self) -> str:
        """Return the selected entity option to represent the entity state."""
        return self.entity_description.current_fn(self._intensity_data)

    @property
    def options(self) -> list[str]:
        """Return a set of selectable options."""
        if options_fn := self.entity_description.options_fn:
            return options_fn(self.get_device())
        return super().options

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        if option == "off":
            job = functools.partial(self.coordinator.api.stop_all, self._device_id)
        elif self.get_device()["controller"] == "away":
            raise PuraApiException(ERROR_AWAY_MODE)
        else:
            job = self.entity_description.select_fn(self, option)
            if not job.keywords["bay"]:
                raise PuraApiException(
                    "No fragrance is currently active. Please select a fragrance before adjusting intensity."
                )

        if await self.hass.async_add_executor_job(job):
            await self.coordinator.async_request_refresh()

    async def async_start_timer(
        self, *, slot: int | None = None, intensity: int, duration: timedelta
    ) -> None:
        """Start a fragrance timer."""
        device = self.get_device()
        if not (fragrance_bays := [i for i in (1, 2) if has_fragrance(device, i)]):
            raise PuraApiException("Diffuser does not have any fragrances")

        if not slot:
            if len(fragrance_bays) == 1:
                slot = fragrance_bays[0]
            else:
                runtime = "wearingTime"
                slot = 1 if device["bay1"][runtime] <= device["bay2"][runtime] else 2
        elif slot not in fragrance_bays:
            raise PuraApiException(f"Slot {slot} does not have a fragrance installed")

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
