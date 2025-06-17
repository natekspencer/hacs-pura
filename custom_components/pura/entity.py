"""Pura entities."""

from __future__ import annotations

from typing import Any

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

PURA_MODEL_MAP = {1: "Wall", 2: "Car", "car": "Car", 3: "Plus", 4: "Mini"}


def determine_pura_model(data: dict[str, Any]) -> str | None:
    """Determine pura device model."""
    if (model := PURA_MODEL_MAP.get(m := data.get("model"), m)) == "Wall":
        version = data.get("hwVersion", "3").split(".", 1)[0]
        model = "3" if version in ("1", "2") else version
    return f"Pura {model}"


def has_fragrance(data: dict, bay: int) -> bool:
    """Check if the specified bay has a fragrance."""
    return bool(data[f"bay{bay}"])


class PuraEntity(CoordinatorEntity[PuraDataUpdateCoordinator]):
    """Base class for Pura entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PuraDataUpdateCoordinator,
        description: EntityDescription,
        device_type: str,
        device_id: str,
    ) -> None:
        """Construct a PuraEntity."""
        super().__init__(coordinator)
        self.entity_description = description
        self._device_type = device_type
        self._device_id = device_id
        self._attr_unique_id = f"{device_id}-{description.key}"

        device = self.get_device()
        name = device["displayName"]["name"]
        self._attr_device_info = DeviceInfo(
            connections={
                (
                    CONNECTION_NETWORK_MAC
                    if device_type in ("wall", "plus")
                    else CONNECTION_BLUETOOTH,
                    format_mac(device_id),
                )
            },
            identifiers={(DOMAIN, device_id)},
            manufacturer="Pura",
            model=determine_pura_model(device),
            name=f"{name} Diffuser",
            suggested_area=name if device_type in ("wall", "plus") else None,
            sw_version=device["fwVersion"],
            hw_version=device["hwVersion"],
        )

    def get_device(self) -> dict | None:
        """Get the device from the coordinator."""
        return self.coordinator.get_device(self._device_type, self._device_id)

    @property
    def _intensity_data(self) -> dict:
        """Get the intensity data."""
        device = self.get_device()
        if (controller := device["controller"]) == "timer":
            return device[controller] | {"controller": controller}
        if controller.isnumeric():
            for schedule in device["schedules"]:
                if str(schedule["number"]) == controller:
                    return schedule | {"controller": "schedule"}
        bay = 0
        if (data := device["bay1"]) and data["activeAt"]:
            bay = 1
        elif (data := device.get("bay2")) and data["activeAt"]:
            bay = 2
        intensity = device["deviceDefaults"][f"bay{bay}Intensity"] if bay else None
        return {"bay": bay, "controller": str(controller), "intensity": intensity}
