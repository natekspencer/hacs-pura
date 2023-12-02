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
from .coordinator import PuraDataUpdateCoordinator
from .entity import PuraEntity, has_fragrance
from .helpers import get_device_id


@dataclass
class RequiredKeysMixin:
    """Required keys mixin."""

    value_fn: Callable[[dict], Any | None]


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

SENSORS: dict[tuple[str, ...], tuple[PuraSensorEntityDescription, ...]] = {
    ("car"): (
        PuraSensorEntityDescription(
            key="fragrance",
            name="Fragrance",
            entity_category=EntityCategory.DIAGNOSTIC,
            icon="mdi:scent",
            available_fn=lambda data: has_fragrance(data, 1),
            value_fn=lambda data: data["bay_1"].get("name"),
        ),
        PuraSensorEntityDescription(
            key="intensity",
            name="Fan intensity",
            entity_category=EntityCategory.DIAGNOSTIC,
            icon="mdi:fan",
            available_fn=lambda data: has_fragrance(data, 1),
            value_fn=lambda data: data["bay_1"]["fan_intensity"],
        ),
        PuraSensorEntityDescription(
            key="last_active",
            name="Last active",
            device_class=SensorDeviceClass.TIMESTAMP,
            entity_category=EntityCategory.DIAGNOSTIC,
            available_fn=lambda data: has_fragrance(data, 1),
            value_fn=lambda data: datetime.fromtimestamp(
                data["bay_1"]["active_at"] / 1000, UTC
            ),
        ),
        PuraSensorEntityDescription(
            key="runtime_remaining",
            name="Runtime remaining",
            device_class=SensorDeviceClass.DURATION,
            entity_category=EntityCategory.DIAGNOSTIC,
            native_unit_of_measurement=UnitOfTime.HOURS,
            state_class=SensorStateClass.MEASUREMENT,
            available_fn=lambda data: has_fragrance(data, 1),
            value_fn=lambda data: data["bay_1"]["wearing_time"],
        ),
    ),
    ("wall"): (
        PuraSensorEntityDescription(
            key="active_fragrance",
            translation_key="active_fragrance",
            icon="mdi:scent",
            value_fn=lambda data: fragrance_name(data[f"bay{bay}"]["code"])
            if (bay := data["deviceActiveState"]["activeBay"])
            else "none",
        ),
        PuraSensorEntityDescription(
            key="bay_1",
            name="Slot 1 fragrance",
            entity_category=EntityCategory.DIAGNOSTIC,
            icon="mdi:scent",
            available_fn=lambda data: has_fragrance(data, 1),
            value_fn=lambda data: fragrance_name(data["bay1"]["code"]),
        ),
        PuraSensorEntityDescription(
            key="bay_1_runtime",
            name="Slot 1 runtime",
            device_class=SensorDeviceClass.DURATION,
            entity_category=EntityCategory.DIAGNOSTIC,
            native_unit_of_measurement=UnitOfTime.SECONDS,
            state_class=SensorStateClass.TOTAL_INCREASING,
            available_fn=lambda data: has_fragrance(data, 1),
            value_fn=lambda data: data["bay1"]["wearingTime"],
        ),
        PuraSensorEntityDescription(
            key="bay_1_installed",
            name="Slot 1 installed",
            device_class=SensorDeviceClass.TIMESTAMP,
            entity_category=EntityCategory.DIAGNOSTIC,
            entity_registry_enabled_default=False,
            available_fn=lambda data: has_fragrance(data, 1),
            value_fn=lambda data: datetime.fromtimestamp(data["bay1"]["id"], UTC),
        ),
        PuraSensorEntityDescription(
            key="bay_2",
            name="Slot 2 fragrance",
            entity_category=EntityCategory.DIAGNOSTIC,
            icon="mdi:scent",
            available_fn=lambda data: has_fragrance(data, 2),
            value_fn=lambda data: fragrance_name(data["bay2"]["code"]),
        ),
        PuraSensorEntityDescription(
            key="bay_2_runtime",
            name="Slot 2 runtime",
            device_class=SensorDeviceClass.DURATION,
            entity_category=EntityCategory.DIAGNOSTIC,
            native_unit_of_measurement=UnitOfTime.SECONDS,
            state_class=SensorStateClass.TOTAL_INCREASING,
            available_fn=lambda data: has_fragrance(data, 2),
            value_fn=lambda data: data["bay2"]["wearingTime"],
        ),
        PuraSensorEntityDescription(
            key="bay_2_installed",
            name="Slot 2 installed",
            device_class=SensorDeviceClass.TIMESTAMP,
            entity_category=EntityCategory.DIAGNOSTIC,
            entity_registry_enabled_default=False,
            available_fn=lambda data: has_fragrance(data, 2),
            value_fn=lambda data: datetime.fromtimestamp(data["bay2"]["id"], UTC),
        ),
        PuraSensorEntityDescription(
            key="controller",
            entity_category=EntityCategory.DIAGNOSTIC,
            translation_key="controller",
            value_fn=lambda data: data["controller"],
            icon_fn=CONTROLLER_ICON.get,
        ),
    ),
}


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
            device_type=device_type,
            device_id=get_device_id(device),
        )
        for device_types, descriptions in SENSORS.items()
        for device_type, devices in coordinator.devices.items()
        if device_type in device_types
        for device in devices
        for description in descriptions
    ]

    if not entities:
        return

    async_add_entities(entities)


class PuraSensorEntity(PuraEntity, SensorEntity):
    """Pura sensor entity."""

    entity_description: PuraSensorEntityDescription

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
