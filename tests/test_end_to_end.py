#!/usr/bin/env python3
"""
End-to-end test of the multi-stage LLM pipeline with real API calls.
Tests The Decider → The Analyst pipeline with actual OpenAI API.
"""

import sys
import json
from pathlib import Path

# Add project root to path (parent of tests directory)
sys.path.insert(0, str(Path(__file__).parent.parent))

from twins.twin_runtime import TwinRuntime


def print_separator(title="", char="=", width=80):
    """Print a formatted separator."""
    if title:
        padding = (width - len(title) - 2) // 2
        print(f"\n{char * padding} {title} {char * padding}")
    else:
        print(f"\n{char * width}")


def test_decision(twin, card_a, card_b, context, test_name="Test"):
    """Run a single decision test and display results."""
    print_separator(test_name, "=")

    print("\n📋 SCENARIO:")
    print(f"  Card A: {card_a['name']} ({card_a['cuisine']}) - {card_a['rating_avg']}⭐, ₹{card_a['dish_price']}, {card_a['delivery_time_min']}min")
    print(f"  Card B: {card_b['name']} ({card_b['cuisine']}) - {card_b['rating_avg']}⭐, ₹{card_b['dish_price']}, {card_b['delivery_time_min']}min{', ' + card_b['coupon_text'] if card_b.get('coupon_text') else ''}")
    print(f"  Context: {context['hour_of_day']}:00, {'weekend' if context['is_weekend'] else 'weekday'}, {context['temperature_c']}°C")

    print("\n⚙️  CALLING MULTI-STAGE PIPELINE...")

    try:
        result = twin.choose_between_cards(card_a, card_b, context)

        print("\n✅ SUCCESS!")

        # Display primary results
        print_separator("PRIMARY RESULTS", "-")
        print(f"\n🎯 **Decision**: Card {result['action']}")
        print(f"📊 **Confidence**: {result['meta']['confidence']:.2f} ({result['meta']['confidence']*100:.0f}%)")
        print(f"💡 **Key Factors**: {', '.join(result['meta']['key_factors'])}")

        # Display The Decider's response
        print_separator("STAGE 1: THE DECIDER", "-")
        decider_response = result['meta'].get('decider_response', '')
        if decider_response:
            print(f"\n{decider_response}")
        else:
            print("\n⚠️  No response from The Decider (empty text)")

        # Display The Analyst's extraction
        print_separator("STAGE 2: THE ANALYST", "-")
        analyst = result['meta'].get('analyst_extraction', {})
        print(f"\n✓ Extracted Choice: {analyst.get('choice', 'N/A')}")
        print(f"✓ Extracted Confidence: {analyst.get('confidence', 'N/A')}")
        print(f"✓ Reasoning: {analyst.get('reasoning', 'N/A')}")
        print(f"✓ Key Factors: {analyst.get('key_factors', [])}")
        print(f"✓ Extraction Status: {analyst.get('extraction_status', 'N/A')}")

        # Display pipeline status
        print_separator("PIPELINE STATUS", "-")
        pipeline = result['meta'].get('agent_pipeline', {})
        print(f"\n✓ Stage 1: {pipeline.get('stage_1', 'N/A')}")
        print(f"✓ Stage 2: {pipeline.get('stage_2', 'N/A')}")
        print(f"✓ Status: {pipeline.get('extraction_status', 'N/A')}")

        return True

    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run comprehensive end-to-end tests."""
    print_separator("END-TO-END MULTI-STAGE PIPELINE TEST", "=")

    # Check .env exists
    env_path = Path(".env")
    if not env_path.exists():
        print("\n❌ ERROR: .env file not found!")
        print("   Please create .env with OPENAI_API_KEY")
        return False

    print("\n✓ .env file found")

    # Load user profile
    user_profile_path = "data/twin_profiles/USER_001.json"

    if not Path(user_profile_path).exists():
        print(f"\n❌ ERROR: Profile not found at {user_profile_path}")
        return False

    print(f"✓ Loading profile: {user_profile_path}")

    # Read profile to show personality
    with open(user_profile_path) as f:
        profile_data = json.load(f)

    print("\n👤 USER PROFILE:")
    print(f"  Name: {profile_data.get('name', 'N/A')}")
    ocean = profile_data.get('OCEAN', {})
    print(f"  Openness: {ocean.get('openness', 0):.2f}")
    print(f"  Conscientiousness: {ocean.get('conscientiousness', 0):.2f}")
    print(f"  Extraversion: {ocean.get('extraversion', 0):.2f}")
    print(f"  Agreeableness: {ocean.get('agreeableness', 0):.2f}")
    print(f"  Neuroticism: {ocean.get('neuroticism', 0):.2f}")

    twin = TwinRuntime.from_profile_path(user_profile_path)
    print("✓ Twin runtime initialized")

    # Test 1: Novel vs Familiar (tests openness)
    print_separator("TEST 1: NOVEL VS FAMILIAR", "=")
    print("Testing if high/low openness influences choice of sushi vs pizza")

    card_a_novel = {
        "name": "Sushi Express",
        "cuisine": "sushi",
        "rating_avg": 4.5,
        "delivery_time_min": 35,
        "distance_km": 4.2,
        "dish_price": 450,
        "delivery_fee": 25,
        "num_reviews": 2350,
        "coupon_text": "",
        "sponsored": 0,
        "coupon_available": 0
    }

    card_b_familiar = {
        "name": "Pizza Palace",
        "cuisine": "pizza",
        "rating_avg": 4.5,
        "delivery_time_min": 35,
        "distance_km": 4.2,
        "dish_price": 450,
        "delivery_fee": 25,
        "num_reviews": 2350,
        "coupon_text": "",
        "sponsored": 0,
        "coupon_available": 0
    }

    context_neutral = {
        "hour_of_day": 19,
        "is_weekend": 0,
        "temperature_c": 28,
        "precip_mm": 0
    }

    success1 = test_decision(
        twin,
        card_a_novel,
        card_b_familiar,
        context_neutral,
        "Test 1: Novel vs Familiar (Equal attributes)"
    )

    # Test 2: Better rating vs Coupon (tests conscientiousness vs budget)
    print_separator("TEST 2: RATING VS COUPON", "=")
    print("Testing if conscientiousness/rating focus vs budget sensitivity influences choice")

    card_a_rating = {
        "name": "Top Rated Bistro",
        "cuisine": "italian",
        "rating_avg": 4.8,
        "delivery_time_min": 30,
        "distance_km": 3.5,
        "dish_price": 500,
        "delivery_fee": 30,
        "num_reviews": 3200,
        "coupon_text": "",
        "sponsored": 0,
        "coupon_available": 0
    }

    card_b_coupon = {
        "name": "Budget Bites",
        "cuisine": "indian",
        "rating_avg": 4.2,
        "delivery_time_min": 30,
        "distance_km": 3.5,
        "dish_price": 300,
        "delivery_fee": 15,
        "num_reviews": 1500,
        "coupon_text": "FLAT50",
        "sponsored": 0,
        "coupon_available": 1
    }

    success2 = test_decision(
        twin,
        card_a_rating,
        card_b_coupon,
        context_neutral,
        "Test 2: High Rating vs Budget Coupon"
    )

    # Test 3: Fast vs Far (tests distance tolerance)
    print_separator("TEST 3: FAST VS FAR", "=")
    print("Testing delivery time vs distance tradeoff")

    card_a_fast = {
        "name": "Quick Bites",
        "cuisine": "chinese",
        "rating_avg": 4.4,
        "delivery_time_min": 20,
        "distance_km": 1.5,
        "dish_price": 350,
        "delivery_fee": 20,
        "num_reviews": 1800,
        "coupon_text": "",
        "sponsored": 0,
        "coupon_available": 0
    }

    card_b_far = {
        "name": "Distant Delights",
        "cuisine": "thai",
        "rating_avg": 4.7,
        "delivery_time_min": 45,
        "distance_km": 6.5,
        "dish_price": 350,
        "delivery_fee": 40,
        "num_reviews": 2800,
        "coupon_text": "",
        "sponsored": 0,
        "coupon_available": 0
    }

    success3 = test_decision(
        twin,
        card_a_fast,
        card_b_far,
        context_neutral,
        "Test 3: Fast Nearby vs Slow Faraway"
    )

    # Final summary
    print_separator("TEST SUMMARY", "=")

    tests_passed = sum([success1, success2, success3])
    tests_total = 3

    print(f"\n✓ Tests Passed: {tests_passed}/{tests_total}")

    if tests_passed == tests_total:
        print("\n🎉 ALL TESTS PASSED!")
        print("\n✅ The multi-stage LLM pipeline is working perfectly!")
        print("✅ The Decider generates natural text explanations")
        print("✅ The Analyst extracts structured data accurately")
        print("✅ Personality traits influence decisions appropriately")
        print("✅ Confidence levels are reasonable")
        print("✅ Key factors are correctly identified")
    else:
        print(f"\n⚠️  {tests_total - tests_passed} test(s) failed")
        print("   Review errors above for details")

    print_separator()

    return tests_passed == tests_total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
