"""Support for Pura switches."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import functools
from typing import Any

from homeassistant.components.switch import (
    SwitchDeviceClass,
    SwitchEntity,
    SwitchEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import PuraConfigEntry
from .coordinator import PuraDataUpdateCoordinator
from .entity import PuraEntity
from .helpers import get_device_id


def build_away_mode_json(entity: PuraSwitchEntity, away_mode: bool) -> dict:
    """Build away mode json."""
    away_mode_details = {"away_mode": away_mode}

    if not away_mode:
        return away_mode_details

    device_location = entity.get_device()["deviceLocation"] or {}
    return away_mode_details | {
        "latitude": device_location.get("latitude") or entity.hass.config.latitude,
        "longitude": device_location.get("longitude") or entity.hass.config.longitude,
        "radius": device_location.get("radius") or 150,
    }


@dataclass
class RequiredKeysMixin:
    """Required keys mixin."""

    lookup_key: str
    toggle_fn: Callable[[PuraEntity, bool], tuple[Callable[..., True], dict]]


@dataclass
class PuraSwitchEntityDescription(SwitchEntityDescription, RequiredKeysMixin):
    """Pura switch entity description."""


SWITCHES: dict[tuple[str, ...], tuple[PuraSwitchEntityDescription, ...]] = {
    ("wall"): (
        PuraSwitchEntityDescription(
            key="ambient_mode",
            name="Ambient mode",
            lookup_key="ambientMode",
            toggle_fn=lambda self, value: (
                self.coordinator.api.set_ambient_mode,
                {"ambient_mode": value},
            ),
        ),
    ),
    ("wall", "plus", "mini"): (
        PuraSwitchEntityDescription(
            key="away_mode",
            name="Away mode",
            lookup_key="awayMode",
            toggle_fn=lambda self, value: (
                self.coordinator.api.set_away_mode,
                build_away_mode_json(self, value),
            ),
        ),
    ),
}


async def async_setup_entry(
    hass: HomeAssistant, entry: PuraConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Pura switchs using config entry."""
    coordinator: PuraDataUpdateCoordinator = entry.runtime_data

    entities = [
        PuraSwitchEntity(
            coordinator=coordinator,
            description=description,
            device_type=device_type,
            device_id=get_device_id(device),
        )
        for device_types, descriptions in SWITCHES.items()
        for device_type, devices in coordinator.devices.items()
        if device_type in device_types
        for device in devices
        for description in descriptions
    ]

    if not entities:
        return

    async_add_entities(entities)


class PuraSwitchEntity(PuraEntity, SwitchEntity):
    """Pura switch."""

    entity_description: PuraSwitchEntityDescription
    _attr_device_class = SwitchDeviceClass.SWITCH
    _attr_entity_category = EntityCategory.CONFIG

    @property
    def is_on(self) -> bool:
        """Return True if the switch is on."""
        return data["enabled"] if isinstance(data := self._data, dict) else data

    @property
    def _data(self) -> dict:
        """Get the fragrance data."""
        return self.get_device().get(self.entity_description.lookup_key)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the switch."""
        await self.async_toggle(value=True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the switch."""
        await self.async_toggle(value=False)

    async def async_toggle(self, **kwargs: Any) -> None:
        """Toggle the switch."""
        _fn, _data = self.entity_description.toggle_fn(self, **kwargs)

        if await self.hass.async_add_executor_job(
            functools.partial(_fn, self._device_id, **_data)
        ):
            await self.coordinator.async_request_refresh()
