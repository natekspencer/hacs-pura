"""Helpers."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any


def first_key_value(
    data: dict[str, Any], keys: Iterable[str], default: Any = None
) -> Any | None:
    """Return the first found key's value in a dictionary."""
    for key in keys:
        if key in data:
            return data[key]
    return default


def get_device_id(data: dict[str, Any]) -> str | None:
    """Get the device id from a dictionary."""
    return data["deviceId"]
