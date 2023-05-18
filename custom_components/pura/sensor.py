"""Support for Pura sensors."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from pypura import fragrance_name

from .const import DOMAIN
from .entity import PuraDataUpdateCoordinator, PuraEntity


@dataclass
class RequiredKeysMixin:
    """Required keys mixin."""

    value_fn: Callable[[dict], Any]


@dataclass
class PuraSensorEntityDescription(SensorEntityDescription, RequiredKeysMixin):
    """Pura sensor entity description."""


SENSORS = (
    PuraSensorEntityDescription(
        key="bay_1",
        name="Slot 1",
        icon="mdi:scent",
        value_fn=lambda data: fragrance_name(data["bay_1"]["code"]),
    ),
    PuraSensorEntityDescription(
        key="bay_1_runtime",
        name="Slot 1 runtime",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        value_fn=lambda data: data["bay_1"]["wearing_time"],
    ),
    PuraSensorEntityDescription(
        key="bay_2",
        name="Slot 2",
        icon="mdi:scent",
        value_fn=lambda data: fragrance_name(data["bay_2"]["code"]),
    ),
    PuraSensorEntityDescription(
        key="bay_2_runtime",
        name="Slot 2 runtime",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        value_fn=lambda data: data["bay_2"]["wearing_time"],
    ),
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
        for description in SENSORS
    ]

    if not entities:
        return

    async_add_entities(entities, True)


class PuraSensorEntity(PuraEntity, SensorEntity):
    """Pura sensor entity."""

    entity_description: PuraSensorEntityDescription
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self) -> str | int | datetime | None:
        """Return the value reported by the sensor."""
        return self.entity_description.value_fn(self.get_device())
