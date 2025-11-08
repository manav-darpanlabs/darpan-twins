#!/usr/bin/env python3
"""Test weather API fixes."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from twins.weather import fetch_current_weather

def test_mumbai_weather():
    """Test Mumbai weather fetch."""
    print("Testing Mumbai weather...")
    print("-" * 60)

    # Mumbai coordinates
    lat = 19.0760
    lon = 72.8777

    result = fetch_current_weather(lat, lon)

    print(f"Temperature: {result.get('temperature_c')}°C")
    print(f"Precipitation: {result.get('precip_mm')}mm")
    print(f"Error: {result.get('error', False)}")

    if result.get('error'):
        print(f"Error message: {result.get('error_message')}")
        print("❌ Weather API returned an error")
        return False

    if result.get('temperature_c') == 0.0:
        print("⚠️ Temperature is 0°C - might be an API issue or actual weather")
        print("   (Winter in Mumbai is ~15-25°C, summer is ~25-35°C)")

    if result.get('hour_of_day'):
        print(f"Hour of day: {result.get('hour_of_day')}")

    if result.get('is_weekend') is not None:
        weekend = "Yes" if result.get('is_weekend') == 1.0 else "No"
        print(f"Is weekend: {weekend}")

    print("-" * 60)

    # Validate temperature is reasonable
    temp = result.get('temperature_c', 0.0)
    if 10 <= temp <= 45:
        print(f"✅ Temperature {temp}°C is within reasonable range for Mumbai")
        return True
    else:
        print(f"⚠️ Temperature {temp}°C might be unusual for Mumbai")
        return False


def test_delhi_weather():
    """Test Delhi weather fetch."""
    print("\nTesting Delhi weather...")
    print("-" * 60)

    # Delhi coordinates
    lat = 28.7041
    lon = 77.1025

    result = fetch_current_weather(lat, lon)

    print(f"Temperature: {result.get('temperature_c')}°C")
    print(f"Precipitation: {result.get('precip_mm')}mm")
    print(f"Error: {result.get('error', False)}")

    if result.get('error'):
        print(f"Error message: {result.get('error_message')}")
        print("❌ Weather API returned an error")
        return False

    print("-" * 60)
    temp = result.get('temperature_c', 0.0)
    if 5 <= temp <= 48:
        print(f"✅ Temperature {temp}°C is within reasonable range for Delhi")
        return True
    else:
        print(f"⚠️ Temperature {temp}°C might be unusual for Delhi")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing Weather API Fixes")
    print("=" * 60)

    mumbai_ok = test_mumbai_weather()
    delhi_ok = test_delhi_weather()

    print("\n" + "=" * 60)
    if mumbai_ok and delhi_ok:
        print("✅ All weather tests passed!")
        print("=" * 60)
        return 0
    else:
        print("⚠️ Some weather tests had issues (check API or internet)")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
