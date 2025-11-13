#!/usr/bin/env python3
"""
Test personality alignment - high-openness users should choose novel cuisines more often.

This script verifies that personality traits influence decision-making as expected.
Specifically, users with high Openness should prefer novel cuisines (sushi, Thai, etc.)
over familiar options (pizza, burgers).

Success criteria: High-openness users choose novel cuisine significantly more than low-openness users
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from twins.twin_profile import TwinProfile
from twins.twin_runtime import TwinRuntime
import argparse


def test_openness_alignment(n: int = 20, verbose: bool = False) -> None:
    """
    Test if high-openness users choose novel cuisines more often.

    Args:
        n: Number of users to test (default: 20)
        verbose: Print details for each user (default: False)
    """
    print(f"\n{'='*60}")
    print(f"PERSONALITY ALIGNMENT TEST")
    print(f"{'='*60}")
    print(f"Testing: Openness → Novel Cuisine Preference")
    print(f"Users to test: {n}")
    print(f"Success: High-openness rate > Low-openness rate")
    print(f"{'='*60}\n")

    # Counters
    high_O_novel = 0  # High-openness users who chose novel (sushi)
    high_O_total = 0  # Total high-openness users
    high_O_users = []

    low_O_novel = 0   # Low-openness users who chose novel (sushi)
    low_O_total = 0   # Total low-openness users
    low_O_users = []

    # Cards: A = novel (sushi), B = familiar (pizza)
    # Make them equal in other attributes to isolate personality effect
    card_a = {
        "name": "Sushi Express",
        "cuisine": "sushi",
        "rating_avg": 4.5,
        "delivery_time_min": 30,
        "distance_km": 3.0,
        "dish_price": 350,
        "delivery_fee": 20,
        "num_reviews": 2000,
        "coupon_text": "",
        "sponsored": 0,
        "coupon_available": 0
    }

    card_b = {
        "name": "Pizza Place",
        "cuisine": "pizza",
        "rating_avg": 4.5,  # Same rating
        "delivery_time_min": 30,  # Same time
        "distance_km": 3.0,  # Same distance
        "dish_price": 350,  # Same price
        "delivery_fee": 20,  # Same fee
        "num_reviews": 2000,  # Same reviews
        "coupon_text": "",
        "sponsored": 0,
        "coupon_available": 0
    }

    context = {
        "hour_of_day": 19,
        "is_weekend": 0,
        "temperature_c": 25,
        "precip_mm": 0
    }

    print("Test Scenario (attributes matched to isolate personality):")
    print(f"  Card A: {card_a['name']} (NOVEL - {card_a['cuisine']}) - ₹{card_a['dish_price']:.0f}, "
          f"{card_a['rating_avg']}⭐, {card_a['delivery_time_min']}min, {card_a['distance_km']:.1f}km")
    print(f"  Card B: {card_b['name']} (FAMILIAR - {card_b['cuisine']}) - ₹{card_b['dish_price']:.0f}, "
          f"{card_b['rating_avg']}⭐, {card_b['delivery_time_min']}min, {card_b['distance_km']:.1f}km")
    print(f"  Context: Evening (19:00), weekday, comfortable temperature\n")

    # Test multiple users
    print(f"Testing {n} users...\n")

    for i in range(1, n + 1):
        user_id = f"user_{i:03d}"
        profile_path = f"data/twin_profiles/{user_id}.json"

        try:
            # Load profile
            profile = TwinProfile.from_json(profile_path)
            twin = TwinRuntime(profile)

            # Make decision
            result = twin.choose_between_cards(card_a, card_b, context)
            choice = result["action"]
            chose_novel = (choice == "A")  # A is sushi (novel)

            # Categorize by openness
            if profile.openness > 0.7:
                high_O_total += 1
                if chose_novel:
                    high_O_novel += 1
                high_O_users.append({
                    "user_id": user_id,
                    "openness": profile.openness,
                    "choice": choice,
                    "chose_novel": chose_novel,
                    "rationale": result.get("rationale", "")[:60]
                })

                if verbose:
                    print(f"  {user_id} (High-O: {profile.openness:.2f}) → {choice} "
                          f"({'✓ Novel' if chose_novel else '✗ Familiar'})")

            elif profile.openness < 0.3:
                low_O_total += 1
                if chose_novel:
                    low_O_novel += 1
                low_O_users.append({
                    "user_id": user_id,
                    "openness": profile.openness,
                    "choice": choice,
                    "chose_novel": chose_novel,
                    "rationale": result.get("rationale", "")[:60]
                })

                if verbose:
                    print(f"  {user_id} (Low-O: {profile.openness:.2f}) → {choice} "
                          f"({'✓ Novel' if chose_novel else '✗ Familiar'})")

            else:
                # Mid-range openness - skip
                if verbose:
                    print(f"  {user_id} (Mid-O: {profile.openness:.2f}) → Skipped")

        except FileNotFoundError:
            if verbose:
                print(f"  {user_id} → Profile not found, skipping")
            continue
        except Exception as e:
            if verbose:
                print(f"  {user_id} → Error: {e}")
            continue

    # Calculate rates
    high_rate = high_O_novel / high_O_total if high_O_total > 0 else 0
    low_rate = low_O_novel / low_O_total if low_O_total > 0 else 0

    # Results
    print(f"\n{'='*60}")
    print("RESULTS")
    print(f"{'='*60}")
    print(f"\nHigh-Openness Users (O > 0.7):")
    print(f"  Total: {high_O_total}")
    print(f"  Chose Novel: {high_O_novel}/{high_O_total} ({high_rate:.1%})")
    print(f"  Chose Familiar: {high_O_total - high_O_novel}/{high_O_total} ({(1-high_rate):.1%})")

    print(f"\nLow-Openness Users (O < 0.3):")
    print(f"  Total: {low_O_total}")
    print(f"  Chose Novel: {low_O_novel}/{low_O_total} ({low_rate:.1%})")
    print(f"  Chose Familiar: {low_O_total - low_O_novel}/{low_O_total} ({(1-low_rate):.1%})")

    print(f"\nComparison:")
    print(f"  High-Openness Novel Rate: {high_rate:.1%}")
    print(f"  Low-Openness Novel Rate: {low_rate:.1%}")
    print(f"  Difference: {abs(high_rate - low_rate):.1%}")

    # Verdict
    if high_O_total == 0 or low_O_total == 0:
        print(f"\nStatus: ⚠️  INSUFFICIENT DATA")
        print(f"  Not enough users with extreme openness values")
        print(f"  Try increasing --users parameter or generating more profiles")
    elif high_rate > low_rate:
        diff = high_rate - low_rate
        print(f"\nStatus: ✓ PASS - Personality alignment confirmed!")
        print(f"  High-openness users chose novel cuisine {diff:.1%} more often")
    elif high_rate == low_rate:
        print(f"\nStatus: ⚠️  NEUTRAL - No personality effect detected")
        print(f"  Consider reviewing prompt's personality guidance")
    else:
        print(f"\nStatus: ✗ FAIL - Inverse personality effect!")
        print(f"  Low-openness users chose novel more often (unexpected)")

    print(f"{'='*60}\n")

    # Show sample decisions if not verbose
    if not verbose and high_O_users and low_O_users:
        print("Sample Decisions:")
        print(f"\nHigh-Openness Sample:")
        for user in high_O_users[:3]:
            print(f"  {user['user_id']} (O={user['openness']:.2f}): {user['choice']} - {user['rationale']}...")

        print(f"\nLow-Openness Sample:")
        for user in low_O_users[:3]:
            print(f"  {user['user_id']} (O={user['openness']:.2f}): {user['choice']} - {user['rationale']}...")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Test personality-driven decision alignment"
    )
    parser.add_argument(
        "--users",
        type=int,
        default=20,
        help="Number of users to test (default: 20)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print details for each user"
    )

    args = parser.parse_args()

    test_openness_alignment(n=args.users, verbose=args.verbose)


if __name__ == "__main__":
    main()
