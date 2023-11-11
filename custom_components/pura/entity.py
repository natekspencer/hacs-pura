"""Pura entities."""
from __future__ import annotations

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
from .helpers import first_key_value

UPDATE_INTERVAL = 30

PURA_MODEL_MAP = {1: "Pura 3", "car": "Pura Car"}


def has_fragrance(data: dict, bay: int) -> bool:
    """Check if the specified bay has a fragrance."""
    return bool(first_key_value(data, (f"bay_{bay}", f"bay{bay}"), {}).get("code"))


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
        name = device["roomName"] if device_type == "wall" else device["device_name"]
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
            model=PURA_MODEL_MAP.get(model := device.get("model"), model),
            name=f"{name} Diffuser",
            suggested_area=name if device_type == "wall" else None,
            sw_version=first_key_value(device, ("fw_version", "fwVersion")),
            hw_version=first_key_value(device, ("hw_version", "hwVersion")),
        )

    def get_device(self) -> dict | None:
        """Get the device from the coordinator."""
        return self.coordinator.get_device(self._device_type, self._device_id)
