"""Support for Pura binary sensors."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import PuraDataUpdateCoordinator, PuraEntity


@dataclass
class RequiredKeysMixin:
    """Required keys mixin."""

    on_fn: Callable[[dict], Any]


@dataclass
class PuraBinarySensorEntityDescription(
    BinarySensorEntityDescription, RequiredKeysMixin
):
    """Pura binary sensor entity description."""


SENSORS = (
    PuraBinarySensorEntityDescription(
        key="connected",
        name="Connected",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        on_fn=lambda data: data["connected"],
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Pura binary_sensors using config entry."""
    coordinator: PuraDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = [
        PuraBinarySensorEntity(
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


class PuraBinarySensorEntity(PuraEntity, BinarySensorEntity):
    """Pura binary sensor entity."""

    entity_description: PuraBinarySensorEntityDescription
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on."""
        return self.entity_description.on_fn(self.get_device())
