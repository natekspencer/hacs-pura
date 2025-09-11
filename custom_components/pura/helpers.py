"""Helpers."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import Any

from homeassistant.util.dt import UTC

PURA_MODEL_MAP = {1: "Wall", 2: "Car", "car": "Car", 3: "Plus", 4: "Mini"}


def determine_pura_model(data: dict[str, Any]) -> str | None:
    """Determine pura device model."""
    if (model := PURA_MODEL_MAP.get(m := data.get("model"), m)) == "Wall":
        version = data.get("hwVersion", "3").split(".", 1)[0]
        model = "3" if version in ("1", "2") else version
    return f"Pura {model}"


def first_key_value(
    data: dict[str, Any], keys: Iterable[str], default: Any = None
) -> Any | None:
    """Return the first found key's value in a dictionary."""
    for key in keys:
        if key in data:
            return data[key]
    return default


def fragrance_remaining(data: dict, bay: int | str) -> float:
    """Return the fragrance remaining."""
    bay_data = data[f"bay{bay}"]
    if (remaining := bay_data.get("remaining")) and "percent" in remaining:
        return remaining["percent"]
    expected_life = bay_data["fragrance"]["expectedLifeHours"] * 3600
    return (max(expected_life - fragrance_runtime(data, bay), 0) / expected_life) * 100


def fragrance_runtime(data: dict, bay: int | str) -> int:
    """Return the fragrance runtime."""
    bay_data = data[f"bay{bay}"]
    wearing_time = bay_data["wearingTime"]
    if (active_at := bay_data["activeAt"]) and not data["lastConnectedAt"]:
        active_time = datetime.now(UTC) - datetime.fromtimestamp(active_at, UTC)
        wearing_time += int(active_time.total_seconds())
    return wearing_time


def get_device_id(data: dict[str, Any]) -> str | None:
    """Get the device id from a dictionary."""
    return data["deviceId"]


def has_fragrance(data: dict, bay: int) -> bool:
    """Check if the specified bay has a fragrance."""
    return bool(data.get(f"bay{bay}"))
