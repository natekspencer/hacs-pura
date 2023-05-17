"""Support for Pura sensors."""
from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from pypura import fragrance_name

from .const import DOMAIN
from .entity import PuraDataUpdateCoordinator, PuraEntity


@dataclass
class RequiredKeysMixin:
    """Required keys mixin."""

    bay: int


@dataclass
class PuraFragranceSensorEntityDescription(SensorEntityDescription, RequiredKeysMixin):
    """Pura fragrance sensor entity description."""


SENSOR_DESCRIPTIONS = (
    PuraFragranceSensorEntityDescription(key="bay_1", name="Slot 1", bay=1),
    PuraFragranceSensorEntityDescription(key="bay_2", name="Slot 2", bay=2),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Pura sensors using config entry."""
    coordinator: PuraDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = [
        PuraSensorEntity(
            coordinator=coordinator,
            config_entry=config_entry,
            description=description,
            device_id=device["device_id"],
        )
        for device_type, devices in coordinator.devices.items()
        if device_type == "wall"
        for device in devices
        for description in SENSOR_DESCRIPTIONS
    ]

    if not entities:
        return

    async_add_entities(entities, True)


class PuraSensorEntity(PuraEntity, SensorEntity):
    """Pura sensor."""

    entity_description: PuraFragranceSensorEntityDescription
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:scent"

    @property
    def native_value(self) -> str:
        """Return the value reported by the sensor."""
        return fragrance_name(self._fragrance_data["code"])

    @property
    def _fragrance_data(self) -> dict:
        """Get the fragrance data."""
        return self.get_device()[f"bay_{self.entity_description.bay}"]
