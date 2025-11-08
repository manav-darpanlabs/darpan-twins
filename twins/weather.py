import requests
from typing import Any, Dict, List
from datetime import datetime


def search_cities(query: str, count: int = 5) -> List[Dict[str, Any]]:
    if not query or len(query.strip()) < 2:
        return []
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": query.strip(), "count": count, "language": "en", "format": "json"}
    try:
        r = requests.get(url, params=params, timeout=8)
        r.raise_for_status()
        data = r.json() or {}
        return data.get("results", []) or []
    except Exception:
        return []


def fetch_current_weather(latitude: float, longitude: float) -> Dict[str, Any]:
    """Fetch current weather from Open-Meteo API with retry logic."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,precipitation",
        "timezone": "auto",
    }

    # Try twice in case of transient failure
    for attempt in range(2):
        try:
            r = requests.get(url, params=params, timeout=10)
            r.raise_for_status()
            data = r.json() or {}
            current = data.get("current", {}) or {}

            # Validate we actually got data
            if not current:
                continue

            temp = float(current.get("temperature_2m", 0.0))
            precip = float(current.get("precipitation", 0.0))

            # If temp is exactly 0.0, it might be an API issue or actual temperature
            # We'll include an 'error' flag if data seems invalid
            time_str = current.get("time")
            hour = None
            is_weekend = None
            try:
                if isinstance(time_str, str) and time_str:
                    # Example: 2025-10-31T13:00 or with offset
                    ts = time_str.replace("Z", "+00:00")
                    dt = datetime.fromisoformat(ts)
                    hour = dt.hour
                    is_weekend = 1 if dt.weekday() >= 5 else 0
            except Exception:
                pass

            out: Dict[str, Any] = {
                "temperature_c": temp,
                "precip_mm": precip,
                "error": False,
            }
            if hour is not None:
                out["hour_of_day"] = float(hour)
            if is_weekend is not None:
                out["is_weekend"] = float(is_weekend)
            return out
        except Exception as e:
            # On last attempt, return error state
            if attempt == 1:
                return {
                    "temperature_c": 0.0,
                    "precip_mm": 0.0,
                    "error": True,
                    "error_message": f"Weather API unavailable: {str(e)[:50]}",
                }
            # Otherwise retry
            continue

    # Fallback if both attempts failed
    return {
        "temperature_c": 0.0,
        "precip_mm": 0.0,
        "error": True,
        "error_message": "Weather API unavailable after retries",
    }


