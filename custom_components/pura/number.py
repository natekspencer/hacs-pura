"""Support for Pura fragrance intensity."""

from __future__ import annotations

import functools

from pypura import PuraApiException

from homeassistant.components.number import NumberEntity, NumberEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import PuraConfigEntry
from .const import ERROR_AWAY_MODE
from .coordinator import PuraDataUpdateCoordinator
from .entity import PuraEntity
from .helpers import get_device_id

NUMBER_DESCRIPTION = NumberEntityDescription(key="intensity", name="Intensity")


async def async_setup_entry(
    hass: HomeAssistant, entry: PuraConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Pura numbers using config entry."""
    coordinator: PuraDataUpdateCoordinator = entry.runtime_data

    entities = [
        PuraNumberEntity(
            coordinator=coordinator,
            description=NUMBER_DESCRIPTION,
            device_type=device_type,
            device_id=get_device_id(device),
        )
        for device_type, devices in coordinator.devices.items()
        if device_type == "wall"
        for device in devices
    ]

    if not entities:
        return

    async_add_entities(entities)


class PuraNumberEntity(PuraEntity, NumberEntity):
    """Pura number."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_max_value: int = 10
    _attr_native_min_value: int = 1

    @property
    def native_value(self) -> int:
        """Return the value reported by the number."""
        return self._intensity_data["intensity"]

    @property
    def _intensity_data(self) -> dict:
        """Get the intensity data."""
        device = self.get_device()
        bay = device["deviceActiveState"]["activeBay"]
        controller = device["controller"]
        intensity = device["deviceActiveState"]["activeBayIntensity"]
        return {"bay": bay, "controller": str(controller), "intensity": intensity}

    async def async_set_native_value(self, value: int) -> None:
        """Update the current value."""
        data = self._intensity_data

        if (controller := data["controller"]) == "away":
            raise PuraApiException(ERROR_AWAY_MODE)
        if not (bay := data["bay"]):
            raise PuraApiException(
                "No fragrance is currently active. Please select a fragrance before adjusting intensity."
            )

        if await self.hass.async_add_executor_job(
            functools.partial(
                self.coordinator.api.set_intensity,
                self._device_id,
                bay=bay,
                controller=controller,
                intensity=value,
            )
        ):
            await self.coordinator.async_request_refresh()
