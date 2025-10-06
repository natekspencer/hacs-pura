"""Pura coordinator."""

from __future__ import annotations

import copy
from datetime import timedelta
import logging
from typing import Any

from deepdiff import DeepDiff
from pypura import Pura
from pypura.ws_subscriber import WebSocketSubscriber

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN
from .helpers import deep_merge, get_device_id

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

        self.subscriber = WebSocketSubscriber(
            session=async_get_clientsession(hass),
            token=client.get_tokens().get("id_token"),
        )
        self.subscriber.start(self._async_handle_message)

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

    async def _async_handle_message(self, data: dict) -> None:
        """Handle a pushed data message."""
        event_type = data.get("eventType")
        record_type = data.get("recordType")
        search = (d for d in self.devices["wall"] if d["deviceId"] == data["deviceId"])
        device = next(search, None)
        handled = False
        if device:
            if event_type == "MODIFY" and record_type == "DEVICE":
                old_device = copy.deepcopy(device)
                deep_merge(device, data.get("deviceRecord"))
                diff = DeepDiff(
                    old_device,
                    device,
                    ignore_order=True,
                    report_repetition=True,
                    verbose_level=2,
                )
                _LOGGER.debug("Devices updated: %s", diff if diff else "no changes")
                handled = True
            elif record_type == "TIMER":
                if event_type == "REMOVE":
                    _LOGGER.debug("Removed timer from device")
                    device["timer"] = None
                    handled = True
                elif event_type in ("INSERT", "MODIFY"):
                    _LOGGER.debug("%s timer on device", event_type.capitalize())
                    device["timer"] = data.get("timerRecord")
                    handled = True

        if handled:
            self.async_set_updated_data(self.devices)
        else:
            _LOGGER.warning("Received unknown update: %s", data)

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


class PuraCarFirmwareDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(self, hass: HomeAssistant, client: Pura) -> None:
        """Initialize."""
        self.api = client

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )

    async def _async_update_data(self):
        """Update data via library, refresh token if necessary."""
        try:
            details: str = await self.hass.async_add_executor_job(
                self.api.get_latest_firmware_details, "car", "v1"
            )
            return {
                (part := line.split("=", 1))[0].lower(): part[1]
                for line in details.split("\n")
            }
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.error(
                "Unknown exception while updating Pura data: %s", err, exc_info=1
            )
            raise UpdateFailed(err) from err
