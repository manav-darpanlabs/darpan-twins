#!/usr/bin/env python3
"""
Quick test of the multi-stage LLM pipeline.

This script tests The Decider → The Analyst pipeline without requiring API keys.
It verifies the code structure and fallback mechanisms work correctly.
"""

import sys
from pathlib import Path

# Add project root to path (parent of tests directory)
sys.path.insert(0, str(Path(__file__).parent.parent))

from twins.twin_runtime import TwinRuntime


def test_pipeline_structure():
    """Test that the pipeline structure works correctly."""
    print("=" * 60)
    print("TESTING MULTI-STAGE LLM PIPELINE")
    print("=" * 60)

    # Load a test user
    user_profile_path = "data/twin_profiles/USER_001.json"

    if not Path(user_profile_path).exists():
        print(f"✗ Error: Profile not found at {user_profile_path}")
        print("  Please ensure user profiles exist in data/twin_profiles/")
        return False

    print(f"✓ Loading profile: {user_profile_path}")
    twin = TwinRuntime.from_profile_path(user_profile_path)

    # Create test cards
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

    print("\n" + "-" * 60)
    print("TEST SCENARIO")
    print("-" * 60)
    print(f"Card A: {card_a['name']} - {card_a['cuisine']}, {card_a['rating_avg']}⭐, ₹{card_a['dish_price']}")
    print(f"Card B: {card_b['name']} - {card_b['cuisine']}, {card_b['rating_avg']}⭐, ₹{card_b['dish_price']}, {card_b['coupon_text']}")
    print(f"Context: {context['hour_of_day']}:00, {'weekend' if context['is_weekend'] else 'weekday'}, {context['temperature_c']}°C")

    print("\n" + "-" * 60)
    print("CALLING MULTI-STAGE PIPELINE...")
    print("-" * 60)

    try:
        result = twin.choose_between_cards(card_a, card_b, context)

        print("\n✓ Pipeline executed successfully!")
        print("\n" + "=" * 60)
        print("RESULTS")
        print("=" * 60)

        # Display primary outputs
        print(f"\n**Choice**: {result['action']}")
        print(f"**Rationale**: {result['rationale'][:150]}...")

        # Display metadata
        meta = result.get('meta', {})
        print(f"\n**Confidence**: {meta.get('confidence', 'N/A')}")
        print(f"**Key Factors**: {meta.get('key_factors', [])}")

        # Display agent pipeline info
        agent_pipeline = meta.get('agent_pipeline', {})
        if agent_pipeline:
            print(f"\n**Agent Pipeline**:")
            print(f"  - Stage 1: {agent_pipeline.get('stage_1', 'N/A')}")
            print(f"  - Stage 2: {agent_pipeline.get('stage_2', 'N/A')}")
            print(f"  - Extraction Status: {agent_pipeline.get('extraction_status', 'N/A')}")

        # Display The Decider's response (full text)
        decider_response = meta.get('decider_response')
        if decider_response:
            print(f"\n**The Decider's Response** (Stage 1):")
            print("-" * 60)
            print(decider_response)
            print("-" * 60)

        # Display The Analyst's extraction
        analyst_extraction = meta.get('analyst_extraction')
        if analyst_extraction:
            print(f"\n**The Analyst's Extraction** (Stage 2):")
            print(f"  - Choice: {analyst_extraction.get('choice', 'N/A')}")
            print(f"  - Confidence: {analyst_extraction.get('confidence', 'N/A')}")
            print(f"  - Reasoning: {analyst_extraction.get('reasoning', 'N/A')}")
            print(f"  - Key Factors: {analyst_extraction.get('key_factors', [])}")
            print(f"  - Extraction Status: {analyst_extraction.get('extraction_status', 'N/A')}")

        print("\n" + "=" * 60)
        print("✓ TEST PASSED - Multi-stage pipeline working!")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n✗ Error during pipeline execution:")
        print(f"  {type(e).__name__}: {e}")
        print("\n" + "-" * 60)
        print("TROUBLESHOOTING:")
        print("-" * 60)
        print("1. Ensure .env file exists with LLM_PROVIDER and API key")
        print("2. Check that RAG examples exist: data/rag_examples.json")
        print("3. Verify OpenAI/Anthropic API key is valid")
        print("\nTo create .env file:")
        print("  cp .env.example .env")
        print("  # Edit .env and add your OPENAI_API_KEY")

        import traceback
        print("\n" + "-" * 60)
        print("FULL TRACEBACK:")
        print("-" * 60)
        traceback.print_exc()

        return False


if __name__ == "__main__":
    success = test_pipeline_structure()
    sys.exit(0 if success else 1)
