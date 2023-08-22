"""Diagnostics support for Pura."""
from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics.util import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import PuraDataUpdateCoordinator

TO_REDACT = {
    CONF_LATITUDE,
    CONF_LONGITUDE,
    "device_id",
    "deviceId",
    "pk",
    "serialNumber",
    "sk",
    "uid",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator: PuraDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    return async_redact_data(coordinator.data, TO_REDACT)
