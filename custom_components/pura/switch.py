"""Support for Pura switches."""
from __future__ import annotations

import functools
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import (
    SwitchDeviceClass,
    SwitchEntity,
    SwitchEntityDescription,
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

    toggle_fn: Callable[[PuraEntity, bool], tuple[Callable[..., True], dict]]


@dataclass
class PuraSwitchEntityDescription(SwitchEntityDescription, RequiredKeysMixin):
    """Pura switch entity description."""


SWITCHES = (
    PuraSwitchEntityDescription(
        key="ambient_mode",
        name="Ambient mode",
        toggle_fn=lambda self, value: (
            self.coordinator.api.set_ambient_mode,
            {"ambient_mode": value},
        ),
    ),
    PuraSwitchEntityDescription(
        key="away_mode",
        name="Away mode",
        toggle_fn=lambda self, value: (
            self.coordinator.api.set_away_mode,
            {"away_mode": value}
            | (
                {
                    k: v
                    for k, v in self.get_device()["device_location"].items()
                    if k in ("radius", "longitude", "latitude")
                }
                if value
                else {}
            ),
        ),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Pura switchs using config entry."""
    coordinator: PuraDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = [
        PuraSwitchEntity(
            coordinator=coordinator,
            config_entry=config_entry,
            description=description,
            device_id=device["device_id"],
        )
        for device_type, devices in coordinator.devices.items()
        if device_type == "wall"
        for device in devices
        for description in SWITCHES
    ]

    if not entities:
        return

    async_add_entities(entities, True)


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
        return self.get_device()[self.entity_description.key]

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
