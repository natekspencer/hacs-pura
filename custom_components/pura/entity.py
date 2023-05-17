"""Pura entities."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, EntityDescription
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)
from pypura import Pura

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
UPDATE_INTERVAL = 30


class PuraDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(self, hass: HomeAssistant, client: Pura) -> None:
        """Initialize."""
        self.api = client
        self.devices: dict[str, list[dict[str, Any]]] = {}

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )

    def get_device(self, device_id: str) -> dict | None:
        """Get device by id."""
        return next(
            (
                device
                for device in self.devices["wall"]
                if device["device_id"] == device_id
            ),
            None,
        )

    async def _async_update_data(self):
        """Update data via library, refresh token if necessary."""
        try:
            if devices := await self.hass.async_add_executor_job(self.api.get_devices):
                self.devices = devices
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.error(
                "Unknown Exception while updating Pura data: %s", err, exc_info=1
            )
            raise UpdateFailed(err) from err
        return self.devices


class PuraEntity(CoordinatorEntity[PuraDataUpdateCoordinator]):
    """Base class for Pura entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PuraDataUpdateCoordinator,
        config_entry: ConfigEntry,
        description: EntityDescription,
        device_id: str,
    ) -> None:
        """Construct a PuraEntity."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self.entity_description = description
        self._device_id = device_id
        self._attr_unique_id = f"{device_id}-{description.key}"

        device = self.get_device()
        name = device["room_name"]
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            manufacturer="Pura",
            model=device.get("model"),
            name=name,
            suggested_area=name,
            sw_version=device["fw_version"],
            hw_version=device["hw_version"],
        )

    def get_device(self) -> Any | None:
        """Get the device from the coordinator."""
        return self.coordinator.get_device(self._device_id)
