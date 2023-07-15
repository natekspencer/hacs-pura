"""Pura entities."""
from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import (
    CONNECTION_BLUETOOTH,
    CONNECTION_NETWORK_MAC,
    format_mac,
)
from homeassistant.helpers.entity import DeviceInfo, EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import PuraDataUpdateCoordinator

UPDATE_INTERVAL = 30


def has_fragrance(data: dict, bay: int) -> bool:
    """Check if the specified bay has a fragrance."""
    return bool(data.get(f"bay_{bay}", {}).get("code"))


class PuraEntity(CoordinatorEntity[PuraDataUpdateCoordinator]):
    """Base class for Pura entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PuraDataUpdateCoordinator,
        config_entry: ConfigEntry,
        description: EntityDescription,
        device_type: str,
        device_id: str,
    ) -> None:
        """Construct a PuraEntity."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self.entity_description = description
        self._device_type = device_type
        self._device_id = device_id
        self._attr_unique_id = f"{device_id}-{description.key}"

        device = self.get_device()
        name = device["room_name"] if device_type == "wall" else device["device_name"]
        self._attr_device_info = DeviceInfo(
            connections={
                (
                    CONNECTION_NETWORK_MAC
                    if device_type == "wall"
                    else CONNECTION_BLUETOOTH,
                    format_mac(device_id),
                )
            },
            identifiers={(DOMAIN, device_id)},
            manufacturer="Pura",
            model=device.get("model"),
            name=f"{name} Diffuser",
            suggested_area=name if device_type == "wall" else None,
            sw_version=device["fw_version"],
            hw_version=device["hw_version"],
        )

    def get_device(self) -> dict | None:
        """Get the device from the coordinator."""
        return self.coordinator.get_device(self._device_type, self._device_id)
