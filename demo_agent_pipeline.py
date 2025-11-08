#!/usr/bin/env python3
"""
Demo of The Decider → The Analyst pipeline with simulated responses.

This demonstrates how the multi-stage pipeline would work with actual LLM responses,
without requiring API keys.
"""

import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from twins.prompts_llm import build_decider_prompt, build_analyst_prompt


def demo_pipeline():
    """Demonstrate the two-stage pipeline with example text."""

    print("=" * 80)
    print(" " * 20 + "MULTI-STAGE LLM PIPELINE DEMO")
    print("=" * 80)
    print()

    # Example user profile
    user_name = "Alice"
    ocean = {
        "openness": 0.73,
        "conscientiousness": 0.52,
        "extraversion": 0.61,
        "agreeableness": 0.48,
        "neuroticism": 0.35
    }

    demographics = {
        "dem_age": 28,
        "dem_income": 750000,
        "dem_gender_male": 0,
        "dem_gender_female": 1,
        "ctx_novelty_seeking": 0.68,
        "ctx_budget_sensitivity": 0.42,
        "ctx_distance_tolerance": 0.55,
        "ctx_rating_focus": 0.62
    }

    context_summary = "19:00 (evening), weekday, 28°C"

    card_a = {
        "name": "Sushi Express",
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

    # STAGE 1: Build The Decider's prompt
    print("━" * 80)
    print("STAGE 1: THE DECIDER")
    print("━" * 80)
    print()

    decider_prompt = build_decider_prompt(
        user_name=user_name,
        ocean=ocean,
        demographics=demographics,
        context_summary=context_summary,
        card_a=card_a,
        card_b=card_b,
        past_decisions=[]
    )

    print("**The Decider's Prompt** (first 500 chars):")
    print("-" * 80)
    print(decider_prompt[:500] + "...")
    print("-" * 80)
    print()

    # Simulated response from The Decider
    decider_response = """I'd choose Card A - the Sushi Express. Even though it's pricier at ₹450 compared to Pizza Palace's ₹280, and the delivery takes longer (35 minutes versus 25), I'm drawn to several key factors here.

First and foremost, the rating difference is significant - 4.7 stars versus 4.3 stars. With my conscientiousness score of 0.52 and rating focus of 0.62, I really value those extra reviews and higher satisfaction scores. The 2,350 reviews for Sushi Express give me confidence that this is a consistently good choice.

Second, as someone with high openness (0.73) and strong novelty-seeking tendencies (0.68), trying sushi is much more appealing than the familiar pizza option. It's evening time, I'm probably looking to treat myself after work, and the exotic cuisine matches my adventurous personality perfectly.

I'm quite confident about this choice - I'd say around 75-80% sure. The main hesitation is the price difference and longer delivery time, but given the context (evening, comfortable weather), I'm willing to wait a bit longer for the better-rated, more exciting option. The rating and novelty factors outweigh the budget concerns for me in this scenario."""

    print("**The Decider's Response** (natural text output):")
    print("-" * 80)
    print(decider_response)
    print("-" * 80)
    print()

    # STAGE 2: Build The Analyst's prompt
    print()
    print("━" * 80)
    print("STAGE 2: THE ANALYST")
    print("━" * 80)
    print()

    analyst_prompt = build_analyst_prompt(decider_response)

    print("**The Analyst's Prompt** (first 500 chars):")
    print("-" * 80)
    print(analyst_prompt[:500] + "...")
    print("-" * 80)
    print()

    # Simulated response from The Analyst
    analyst_response = {
        "choice": "A",
        "confidence": 0.78,
        "reasoning": "Chose Card A (Sushi Express) due to significantly better rating (4.7⭐ vs 4.3⭐) and novel cuisine that aligns with high openness personality, outweighing higher price and longer delivery time.",
        "key_factors": ["rating", "cuisine", "novelty", "personality_fit", "reviews"]
    }

    print("**The Analyst's Extraction** (structured JSON output):")
    print("-" * 80)
    print(json.dumps(analyst_response, indent=2))
    print("-" * 80)
    print()

    # FINAL OUTPUT
    print()
    print("━" * 80)
    print("FINAL OUTPUT (Combined)")
    print("━" * 80)
    print()

    print(f"**Choice**: {analyst_response['choice']}")
    print(f"**Confidence**: {analyst_response['confidence']} (78%)")
    print(f"**Reasoning**: {analyst_response['reasoning']}")
    print(f"**Key Factors**: {', '.join(analyst_response['key_factors'])}")
    print()

    print("**Agent Pipeline**:")
    print(f"  ✓ Stage 1: The Decider (natural text generation)")
    print(f"  ✓ Stage 2: The Analyst (information extraction)")
    print(f"  ✓ Status: success")
    print()

    print("=" * 80)
    print("✓ DEMO COMPLETE")
    print("=" * 80)
    print()
    print("**Key Benefits of Multi-Stage Approach**:")
    print("  1. Natural, personality-driven explanations from The Decider")
    print("  2. Structured, parseable data from The Analyst")
    print("  3. Clear separation of concerns (generation vs extraction)")
    print("  4. Easier to debug (can inspect both stages independently)")
    print("  5. Fallback mechanism if extraction fails")
    print()


if __name__ == "__main__":
    demo_pipeline()
