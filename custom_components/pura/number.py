"""Support for Pura fragrance intensity."""
from __future__ import annotations

import functools

from pypura import PuraApiException

from homeassistant.components.number import NumberEntity, NumberEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, ERROR_AWAY_MODE
from .entity import PuraDataUpdateCoordinator, PuraEntity

NUMBER_DESCRIPTION = NumberEntityDescription(key="intensity", name="Intensity")


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Pura numbers using config entry."""
    coordinator: PuraDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = [
        PuraNumberEntity(
            coordinator=coordinator,
            config_entry=config_entry,
            description=NUMBER_DESCRIPTION,
            device_id=device["device_id"],
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
        if (controller := device["controller"]) == "schedule":
            controller = device["controlling_schedule"]
            bay = (schedule := device["schedules"][controller])["bay"]
            intensity = schedule["intensity"]
        elif controller == "timer":
            bay = (timer := device["timer"])["bay"]
            intensity = timer["intensity"]
        else:
            defaults = device["device_defaults"]
            if device["bay_1"]["active_at"]:
                bay = 1
                intensity = defaults["bay_1_intensity"]
            elif device["bay_2"]["active_at"]:
                bay = 2
                intensity = defaults["bay_2_intensity"]
            else:  # fragrance is off
                bay = 0
                intensity = 0
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
