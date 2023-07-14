"""Support for Pura sensors."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from pypura import fragrance_name

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util.dt import UTC

from .const import DOMAIN
from .entity import PuraDataUpdateCoordinator, PuraEntity, has_fragrance


@dataclass
class RequiredKeysMixin:
    """Required keys mixin."""

    value_fn: Callable[[dict], Any]


@dataclass
class PuraSensorEntityDescription(SensorEntityDescription, RequiredKeysMixin):
    """Pura sensor entity description."""

    available_fn: Callable[[dict], bool] | None = None
    icon_fn: Callable[[str], str | None] | None = None


CONTROLLER_ICON = {
    "away": "mdi:map-marker-radius-outline",
    "default": "mdi:toggle-switch-outline",
    "schedule": "mdi:calendar-blank-outline",
    "timer": "mdi:timer-outline",
}

SENSORS = (
    PuraSensorEntityDescription(
        key="bay_1",
        name="Slot 1 fragrance",
        icon="mdi:scent",
        available_fn=lambda data: has_fragrance(data, 1),
        value_fn=lambda data: fragrance_name(data["bay_1"]["code"]),
    ),
    PuraSensorEntityDescription(
        key="bay_1_runtime",
        name="Slot 1 runtime",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        available_fn=lambda data: has_fragrance(data, 1),
        value_fn=lambda data: data["bay_1"]["wearing_time"],
    ),
    PuraSensorEntityDescription(
        key="bay_1_installed",
        name="Slot 1 installed",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_registry_enabled_default=False,
        available_fn=lambda data: has_fragrance(data, 1),
        value_fn=lambda data: datetime.fromtimestamp(data["bay_1"]["id"], UTC),
    ),
    PuraSensorEntityDescription(
        key="bay_2",
        name="Slot 2 fragrance",
        icon="mdi:scent",
        available_fn=lambda data: has_fragrance(data, 2),
        value_fn=lambda data: fragrance_name(data["bay_2"]["code"]),
    ),
    PuraSensorEntityDescription(
        key="bay_2_runtime",
        name="Slot 2 runtime",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        available_fn=lambda data: has_fragrance(data, 2),
        value_fn=lambda data: data["bay_2"]["wearing_time"],
    ),
    PuraSensorEntityDescription(
        key="bay_2_installed",
        name="Slot 2 installed",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_registry_enabled_default=False,
        available_fn=lambda data: has_fragrance(data, 2),
        value_fn=lambda data: datetime.fromtimestamp(data["bay_2"]["id"], UTC),
    ),
    PuraSensorEntityDescription(
        key="controller",
        name="Controller",
        translation_key="controller",
        value_fn=lambda data: data["controller"],
        icon_fn=CONTROLLER_ICON.get,
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

    async_add_entities(entities)


class PuraSensorEntity(PuraEntity, SensorEntity):
    """Pura sensor entity."""

    entity_description: PuraSensorEntityDescription
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        if available_fn := self.entity_description.available_fn:
            return available_fn(self.get_device())
        return super().available

    @property
    def icon(self) -> str | None:
        """Return the icon to use in the frontend, if any."""
        if icon_fn := self.entity_description.icon_fn:
            return icon_fn(self.native_value)
        return super().icon

    @property
    def native_value(self) -> str | int | datetime | None:
        """Return the value reported by the sensor."""
        return self.entity_description.value_fn(self.get_device())
