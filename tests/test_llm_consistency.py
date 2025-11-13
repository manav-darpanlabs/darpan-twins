#!/usr/bin/env python3
"""
Test LLM consistency - same input should produce same output.

This script tests if the LLM-based twin makes consistent decisions
when presented with the same choice multiple times.

Success criteria: >80% consistency (8/10 runs should choose the same card)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from twins.twin_runtime import TwinRuntime
from collections import Counter
import argparse


def test_consistency(user_id: str = "user_001", n: int = 10) -> None:
    """
    Test consistency of LLM decision-making.

    Args:
        user_id: User profile to test
        n: Number of runs (default: 10)
    """
    print(f"\n{'='*60}")
    print(f"LLM CONSISTENCY TEST")
    print(f"{'='*60}")
    print(f"User: {user_id}")
    print(f"Runs: {n}")
    print(f"Target: >80% consistency (8/{n})")
    print(f"{'='*60}\n")

    # Load twin
    profile_path = f"data/twin_profiles/{user_id}.json"
    print(f"Loading twin profile from {profile_path}...")
    try:
        twin = TwinRuntime.from_profile_path(profile_path)
        print(f"✓ Loaded twin: {twin.profile.user_id}")
        print(f"  Personality: O={twin.profile.openness:.2f}, C={twin.profile.conscientiousness:.2f}, "
              f"E={twin.profile.extraversion:.2f}, A={twin.profile.agreeableness:.2f}, N={twin.profile.neuroticism:.2f}\n")
    except FileNotFoundError:
        print(f"✗ Error: Profile not found at {profile_path}")
        print(f"  Please ensure the profile exists or try a different user_id")
        return
    except Exception as e:
        print(f"✗ Error loading profile: {e}")
        return

    # Define test scenario
    card_a = {
        "name": "Sushi Hub",
        "cuisine": "sushi",
        "rating_avg": 4.7,
        "delivery_time_min": 35,
        "distance_km": 4.2,
        "dish_price": 450,
        "delivery_fee": 25,
        "num_reviews": 2350,
        "coupon_text": "",
        "sponsored": 0,
        "coupon_available": 0
    }

    card_b = {
        "name": "Pizza Palace",
        "cuisine": "pizza",
        "rating_avg": 4.3,
        "delivery_time_min": 25,
        "distance_km": 2.1,
        "dish_price": 280,
        "delivery_fee": 15,
        "num_reviews": 1840,
        "coupon_text": "FLAT20",
        "sponsored": 0,
        "coupon_available": 1
    }

    context = {
        "hour_of_day": 19,
        "is_weekend": 0,
        "temperature_c": 28,
        "precip_mm": 0
    }

    print("Test Scenario:")
    print(f"  Card A: {card_a['name']} ({card_a['cuisine']}) - ₹{card_a['dish_price']:.0f}, "
          f"{card_a['rating_avg']}⭐, {card_a['delivery_time_min']}min, {card_a['distance_km']:.1f}km")
    print(f"  Card B: {card_b['name']} ({card_b['cuisine']}) - ₹{card_b['dish_price']:.0f}, "
          f"{card_b['rating_avg']}⭐, {card_b['delivery_time_min']}min, {card_b['distance_km']:.1f}km, {card_b['coupon_text']}")
    print(f"  Context: {context['hour_of_day']}:00, weekday, {context['temperature_c']}°C, no rain\n")

    # Run consistency test
    print(f"Running {n} decision rounds...\n")
    choices = []
    rationales = []
    confidences = []

    for i in range(n):
        try:
            result = twin.choose_between_cards(card_a, card_b, context)
            choice = result["action"]
            rationale = result.get("rationale", "")
            confidence = result.get("meta", {}).get("confidence", 0.5)

            choices.append(choice)
            rationales.append(rationale)
            confidences.append(confidence)

            print(f"  Run {i+1}/{n}: {choice} (confidence: {confidence:.2f})")
            print(f"           {rationale[:80]}{'...' if len(rationale) > 80 else ''}")

        except Exception as e:
            print(f"  Run {i+1}/{n}: ✗ Error - {e}")
            choices.append("ERROR")
            rationales.append(str(e))
            confidences.append(0.0)

    # Calculate consistency
    counter = Counter(choices)
    most_common = counter.most_common(1)[0]
    consistency_rate = most_common[1] / n
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

    print(f"\n{'='*60}")
    print("RESULTS")
    print(f"{'='*60}")
    print(f"Choice Distribution:")
    for choice, count in counter.most_common():
        percentage = count / n * 100
        bar = "█" * int(percentage / 2)
        print(f"  {choice}: {count}/{n} ({percentage:.1f}%) {bar}")

    print(f"\nConsistency: {consistency_rate:.1%} ({most_common[1]}/{n} chose '{most_common[0]}')")
    print(f"Avg Confidence: {avg_confidence:.2f}")
    print(f"Target: >80% consistency")

    if consistency_rate >= 0.8:
        print(f"Status: ✓ PASS - LLM is consistent!")
    else:
        print(f"Status: ✗ FAIL - LLM is inconsistent (consider adjusting temperature or prompt)")

    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Test LLM consistency in decision-making"
    )
    parser.add_argument(
        "--user_id",
        type=str,
        default="user_001",
        help="User profile ID to test (default: user_001)"
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=10,
        help="Number of test runs (default: 10)"
    )

    args = parser.parse_args()

    test_consistency(user_id=args.user_id, n=args.runs)


if __name__ == "__main__":
    main()
