"""Pura coordinator."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from deepdiff import DeepDiff
from pypura import Pura

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN
from .helpers import get_device_id

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

    def get_device(self, device_type: str, device_id: str) -> dict | None:
        """Get device by type and id."""
        return next(
            (
                device
                for device in self.devices[device_type]
                if get_device_id(device) == device_id
            ),
            None,
        )

    async def _async_update_data(self):
        """Update data via library, refresh token if necessary."""
        try:
            if devices := await self.hass.async_add_executor_job(self.api.get_devices):
                diff = DeepDiff(
                    self.devices,
                    devices,
                    ignore_order=True,
                    report_repetition=True,
                    verbose_level=2,
                )
                _LOGGER.debug("Devices updated: %s", diff if diff else "no changes")
                self.devices = devices
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.error(
                "Unknown exception while updating Pura data: %s", err, exc_info=1
            )
            raise UpdateFailed(err) from err
        return self.devices
