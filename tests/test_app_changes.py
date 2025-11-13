#!/usr/bin/env python3
"""Test script to verify app_streamlit.py changes work correctly."""

import sys
import os

# Add project root to path (parent of tests directory)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the functions we modified
from app_streamlit import format_factor, aggregate_results, DEFAULT_CITIES


def test_format_factor():
    """Test the format_factor function."""
    print("Testing format_factor()...")

    test_cases = [
        ("higher average rating (4.3 vs 3.9)", "Higher Rating"),
        ("lower price makes it more appealing", "Lower Price"),
        ("more reviews (700 vs 12000) indicates a good level of trust", "More Reviews"),
        ("faster delivery time", "Faster Delivery"),
        ("coupon available", "Coupon Available"),
        ("novel cuisine experience", "Novel Cuisine"),
        ("friend endorsed this restaurant", "Friend Endorsed"),
        ("Some Unknown Reason", "Some Unknown Reason"),
    ]

    passed = 0
    failed = 0

    for input_text, expected in test_cases:
        result = format_factor(input_text)
        if result == expected:
            print(f"  ✓ '{input_text[:40]}...' -> '{result}'")
            passed += 1
        else:
            print(f"  ✗ '{input_text[:40]}...' -> Expected '{expected}', got '{result}'")
            failed += 1

    print(f"  Result: {passed} passed, {failed} failed\n")
    return failed == 0


def test_aggregate_results():
    """Test the aggregate_results function."""
    print("Testing aggregate_results()...")

    # Mock data simulating run_dual_llm_for_users output
    mock_results = [
        {
            "user_id": "user_001",
            "name": "Alice",
            "action": "A",
            "reasons": ["higher average rating (4.3 vs 3.9)", "faster delivery time"],
            "checks": {"price": "B", "delivery": "A", "fit": "A", "trust": "A"},
            "response_A": "I like this",
            "response_B": "Not bad",
            "likert": 4,
        },
        {
            "user_id": "user_002",
            "name": "Bob",
            "action": "A",
            "reasons": ["more reviews indicates trust", "higher rating"],
            "checks": {"price": "B", "delivery": "A", "fit": "tie", "trust": "A"},
            "response_A": "Good choice",
            "response_B": "Okay",
            "likert": 5,
        },
        {
            "user_id": "user_003",
            "name": "Carol",
            "action": "B",
            "reasons": ["lower price makes it more affordable", "coupon available"],
            "checks": {"price": "B", "delivery": "B", "fit": "B", "trust": "tie"},
            "response_A": "Too expensive",
            "response_B": "Great deal",
            "likert": 4,
        },
        {
            "user_id": "user_004",
            "name": "David",
            "action": "tie",
            "reasons": [],
            "checks": {"price": "tie", "delivery": "tie", "fit": "tie", "trust": "tie"},
            "response_A": "Unsure",
            "response_B": "Also unsure",
            "likert": 3,
        },
    ]

    result = aggregate_results(mock_results)

    # Verify structure
    assert "total_twins" in result, "Missing total_twins"
    assert "counts" in result, "Missing counts"
    assert "percent" in result, "Missing percent"
    assert "top_a_factors" in result, "Missing top_a_factors"
    assert "top_b_factors" in result, "Missing top_b_factors"
    assert "checks_breakdown" in result, "Missing checks_breakdown"

    # Verify values
    assert result["total_twins"] == 4, f"Expected 4 twins, got {result['total_twins']}"
    assert result["counts"]["A"] == 2, f"Expected 2 A choices, got {result['counts']['A']}"
    assert result["counts"]["B"] == 1, f"Expected 1 B choice, got {result['counts']['B']}"
    assert result["counts"]["tie"] == 1, f"Expected 1 tie, got {result['counts']['tie']}"

    # Verify percentages
    assert result["percent"]["A"] == 50.0, f"Expected 50% for A, got {result['percent']['A']}"
    assert result["percent"]["B"] == 25.0, f"Expected 25% for B, got {result['percent']['B']}"

    # Verify top factors exist
    assert len(result["top_a_factors"]) > 0, "Expected top_a_factors to have entries"
    assert len(result["top_b_factors"]) > 0, "Expected top_b_factors to have entries"

    # Verify checks breakdown
    assert "price" in result["checks_breakdown"], "Missing price in checks"
    assert "delivery" in result["checks_breakdown"], "Missing delivery in checks"

    print("  ✓ total_twins: 4")
    print("  ✓ counts: A=2, B=1, tie=1")
    print("  ✓ percentages: A=50%, B=25%, tie=25%")
    print(f"  ✓ top_a_factors: {len(result['top_a_factors'])} factors")
    print(f"  ✓ top_b_factors: {len(result['top_b_factors'])} factors")
    print(f"  ✓ checks_breakdown: {list(result['checks_breakdown'].keys())}")
    print("  Result: All checks passed\n")
    return True


def test_default_cities():
    """Test that DEFAULT_CITIES is properly defined."""
    print("Testing DEFAULT_CITIES...")

    assert len(DEFAULT_CITIES) == 8, f"Expected 8 cities, got {len(DEFAULT_CITIES)}"

    expected_cities = ["Mumbai", "Delhi", "Bangalore", "Chennai", "Kolkata", "Hyderabad", "Pune", "Ahmedabad"]
    actual_cities = [c["name"] for c in DEFAULT_CITIES]

    for expected in expected_cities:
        assert expected in actual_cities, f"Missing expected city: {expected}"

    # Verify structure
    for city in DEFAULT_CITIES:
        assert "name" in city, f"Missing 'name' in city: {city}"
        assert "latitude" in city, f"Missing 'latitude' in city: {city}"
        assert "longitude" in city, f"Missing 'longitude' in city: {city}"
        assert "country_code" in city, f"Missing 'country_code' in city: {city}"

    print(f"  ✓ {len(DEFAULT_CITIES)} cities defined")
    print(f"  ✓ Cities: {', '.join(actual_cities)}")
    print("  ✓ All cities have required fields")
    print("  Result: All checks passed\n")
    return True


def main():
    """Run all tests."""
    print("="*60)
    print("Testing app_streamlit.py modifications")
    print("="*60)
    print()

    all_passed = True

    try:
        all_passed &= test_format_factor()
    except Exception as e:
        print(f"  ✗ test_format_factor failed with error: {e}\n")
        all_passed = False

    try:
        all_passed &= test_aggregate_results()
    except Exception as e:
        print(f"  ✗ test_aggregate_results failed with error: {e}\n")
        all_passed = False

    try:
        all_passed &= test_default_cities()
    except Exception as e:
        print(f"  ✗ test_default_cities failed with error: {e}\n")
        all_passed = False

    print("="*60)
    if all_passed:
        print("✓ All tests passed!")
        print("="*60)
        return 0
    else:
        print("✗ Some tests failed")
        print("="*60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
