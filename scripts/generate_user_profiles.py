#!/usr/bin/env python3
"""
Generate synthetic user profiles with realistic OCEAN traits and demographics.
Uses LLM to create coherent personality combinations and simulated survey responses.
"""

import os
import sys
import json
import argparse
import time
from pathlib import Path
from typing import Dict, Any, List
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from twins.tools import LLMClient


def generate_profile_with_llm(llm_client: LLMClient, user_id: str, seed: int) -> Dict[str, Any]:
    """
    Generate a single user profile using LLM for realistic trait combinations.

    Args:
        llm_client: LLM client instance
        user_id: User ID (e.g., "USER_011")
        seed: Random seed for reproducibility

    Returns:
        User profile dictionary
    """
    np.random.seed(seed)

    # Generate realistic demographics first using distributions
    age = generate_realistic_age()
    gender = generate_realistic_gender()
    income = generate_realistic_income(age)
    pob_income = generate_realistic_pob_income()
    pob_variety = generate_realistic_food_variety()

    # Create LLM prompt to generate coherent OCEAN traits
    prompt = f"""Generate a realistic personality profile for a food delivery app user with the following demographics:
- Age: {age}
- Gender: {gender}
- Annual Income: ₹{income:,.0f}
- From area with average income: ₹{pob_income:,.0f}

Provide OCEAN personality traits (0.0 to 1.0 scale) that form a coherent personality:
- Openness: How open to new experiences and cuisines
- Conscientiousness: How organized and careful with decisions
- Extraversion: How social and outgoing
- Agreeableness: How cooperative and considerate
- Neuroticism: How anxious and emotional

Also simulate responses to these 5 food delivery behavior questions (1-5 scale):
1. How often do you order food delivery? (1=rarely, 5=very often)
2. How important is restaurant rating (4.5+ stars)? (1=not important, 5=very important)
3. How far are you willing to travel for food? (1=very close only, 5=anywhere)
4. Do you actively seek discounts/coupons? (1=never, 5=always)
5. How adventurous with new cuisines? (1=stick to familiar, 5=love exploring)

Return ONLY valid JSON in this exact format:
{{
  "OCEAN": {{
    "openness": 0.X,
    "conscientiousness": 0.X,
    "extraversion": 0.X,
    "agreeableness": 0.X,
    "neuroticism": 0.X
  }},
  "survey_responses": {{
    "order_frequency": X,
    "rating_importance": X,
    "distance_willingness": X,
    "discount_seeking": X,
    "cuisine_adventurousness": X
  }}
}}

Make the traits realistic and internally consistent. For example:
- High openness usually correlates with cuisine adventurousness
- High conscientiousness correlates with rating importance
- High neuroticism might increase rating importance (risk aversion)"""

    # Try to get LLM-generated profile
    llm_response = llm_client.generate(prompt, temperature=0.8, max_tokens=400)

    if llm_response:
        try:
            # Parse LLM response
            llm_data = json.loads(llm_response)
            ocean = llm_data.get("OCEAN", {})
            survey = llm_data.get("survey_responses", {})

            # Validate OCEAN traits
            if all(k in ocean for k in ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]):
                # Clamp values to 0-1 range
                for key in ocean:
                    ocean[key] = max(0.0, min(1.0, float(ocean[key])))
            else:
                # Fallback to rule-based if LLM response is invalid
                ocean = generate_fallback_ocean(age, income, gender)
                survey = None
        except (json.JSONDecodeError, ValueError, KeyError):
            # Fallback to rule-based if parsing fails
            ocean = generate_fallback_ocean(age, income, gender)
            survey = None
    else:
        # Fallback to rule-based if LLM is unavailable
        ocean = generate_fallback_ocean(age, income, gender)
        survey = None

    # Build profile
    profile = {
        "user_id": user_id,
        "name": f"User {user_id.split('_')[1]}",
        "OCEAN": ocean,
        "demographics": {
            "age": int(age),
            "gender": gender,
            "income": float(income),
            "place_of_birth_avg_income": float(pob_income),
            "place_of_birth_food_variety_index": float(pob_variety)
        }
    }

    # Add survey responses if available (for future use)
    if survey:
        profile["survey_responses"] = survey

    return profile


def generate_realistic_age() -> int:
    """Generate realistic age distribution for food delivery users (skewed toward young adults)."""
    # Beta distribution to create realistic age distribution
    # Most users are 22-35, with tail extending to 65
    age_normalized = np.random.beta(2, 5)  # Skewed toward younger
    age = int(18 + age_normalized * (65 - 18))
    return np.clip(age, 18, 65)


def generate_realistic_gender() -> str:
    """Generate realistic gender distribution."""
    rand = np.random.random()
    if rand < 0.48:
        return "male"
    elif rand < 0.96:
        return "female"
    else:
        return "other"


def generate_realistic_income(age: int) -> float:
    """Generate realistic income based on age (log-normal distribution)."""
    # Base income with age adjustment
    # Younger people (22-30) typically earn less than those 35-50
    age_factor = 1.0
    if age < 25:
        age_factor = 0.6
    elif age < 30:
        age_factor = 0.8
    elif age >= 45:
        age_factor = 1.3

    # Log-normal distribution with realistic parameters for India
    mean_log = np.log(600000 * age_factor)  # Mean ₹600K adjusted by age
    std_log = 0.6  # Creates realistic spread

    income = np.random.lognormal(mean_log, std_log)

    # Clamp to reasonable range
    return np.clip(income, 100000, 5000000)


def generate_realistic_pob_income() -> float:
    """Generate place of birth average income (lower than personal income)."""
    mean_log = np.log(300000)
    std_log = 0.7
    pob_income = np.random.lognormal(mean_log, std_log)
    return np.clip(pob_income, 50000, 2000000)


def generate_realistic_food_variety() -> float:
    """Generate food variety index for place of birth."""
    # Normal distribution centered at 0.6 (most places have moderate variety)
    variety = np.random.normal(0.6, 0.2)
    return np.clip(variety, 0.0, 1.0)


def generate_fallback_ocean(age: int, income: float, gender: str) -> Dict[str, float]:
    """
    Generate OCEAN traits using rule-based approach when LLM is unavailable.
    Creates realistic correlations based on psychology research.
    """
    # Base distributions (normal around 0.5 with realistic variance)
    openness = np.random.normal(0.55, 0.15)  # Slightly above average (self-selection for food delivery)
    conscientiousness = np.random.normal(0.50, 0.18)
    extraversion = np.random.normal(0.50, 0.18)
    agreeableness = np.random.normal(0.55, 0.15)  # Slightly above average
    neuroticism = np.random.normal(0.45, 0.18)  # Slightly below average

    # Age adjustments (based on personality development research)
    if age < 25:
        openness += 0.05  # Younger people more open
        conscientiousness -= 0.08  # Less conscientious when young
        neuroticism += 0.05  # More neurotic when young
    elif age > 50:
        openness -= 0.08  # Older people less open
        conscientiousness += 0.10  # More conscientious with age
        agreeableness += 0.05  # More agreeable with age
        neuroticism -= 0.08  # Less neurotic with age

    # Income adjustments (weak correlations from research)
    income_percentile = min(income / 3000000, 1.0)  # Normalize to 0-1
    if income_percentile > 0.7:  # High income
        conscientiousness += 0.05
        neuroticism -= 0.03

    # Add small correlations between traits (realistic psychology)
    # Openness-Extraversion correlation (r ≈ 0.2)
    if openness > 0.6:
        extraversion += 0.05

    # Conscientiousness-Neuroticism negative correlation (r ≈ -0.3)
    if conscientiousness > 0.6:
        neuroticism -= 0.08

    # Clamp all values to valid range
    ocean = {
        "openness": float(np.clip(openness, 0.0, 1.0)),
        "conscientiousness": float(np.clip(conscientiousness, 0.0, 1.0)),
        "extraversion": float(np.clip(extraversion, 0.0, 1.0)),
        "agreeableness": float(np.clip(agreeableness, 0.0, 1.0)),
        "neuroticism": float(np.clip(neuroticism, 0.0, 1.0))
    }

    return ocean


def main():
    parser = argparse.ArgumentParser(
        description="Generate synthetic user profiles with OCEAN traits and demographics"
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="data/twin_profiles",
        help="Directory to save user profile JSONs"
    )
    parser.add_argument(
        "--start_id",
        type=int,
        default=11,
        help="Starting user ID number (default: 11 for USER_011)"
    )
    parser.add_argument(
        "--end_id",
        type=int,
        default=1000,
        help="Ending user ID number (default: 1000 for USER_1000)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Base random seed for reproducibility"
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        default=50,
        help="Save progress every N profiles (for checkpoint recovery)"
    )

    args = parser.parse_args()

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize LLM client
    print("Initializing LLM client...")
    llm_client = LLMClient()

    if llm_client.provider == "none":
        print("⚠️  WARNING: No LLM provider configured (.env not found or no API key)")
        print("⚠️  Will use rule-based fallback for all profiles")
        print("⚠️  To use LLM: Set LLM_PROVIDER and OPENAI_API_KEY (or ANTHROPIC_API_KEY) in .env file")
    else:
        print(f"✓ LLM provider: {llm_client.provider} (model: {llm_client.model})")

    print(f"\nGenerating user profiles from USER_{args.start_id:03d} to USER_{args.end_id:03d}...")
    print(f"Output directory: {output_dir}")
    print(f"Total profiles to generate: {args.end_id - args.start_id + 1}")
    print("-" * 60)

    successful = 0
    failed = 0
    start_time = time.time()

    for user_num in range(args.start_id, args.end_id + 1):
        user_id = f"USER_{user_num:03d}"
        profile_path = output_dir / f"{user_id}.json"

        # Skip if already exists
        if profile_path.exists():
            print(f"⊘ {user_id} - Already exists, skipping")
            successful += 1
            continue

        try:
            # Generate profile with unique seed per user
            profile = generate_profile_with_llm(
                llm_client=llm_client,
                user_id=user_id,
                seed=args.seed + user_num
            )

            # Save to JSON
            with open(profile_path, 'w') as f:
                json.dump(profile, f, indent=2)

            successful += 1

            # Progress update
            if successful % 10 == 0:
                elapsed = time.time() - start_time
                rate = successful / elapsed
                remaining = (args.end_id - user_num)
                eta = remaining / rate if rate > 0 else 0
                print(f"✓ {user_id} - Progress: {successful}/{args.end_id - args.start_id + 1} "
                      f"({successful/(args.end_id - args.start_id + 1)*100:.1f}%) "
                      f"| Rate: {rate:.1f} profiles/sec | ETA: {eta/60:.1f} min")

            # Small delay to avoid rate limiting (if using LLM)
            if llm_client.provider != "none":
                time.sleep(0.1)  # 10 requests per second max

        except Exception as e:
            print(f"✗ {user_id} - Error: {e}")
            failed += 1
            continue

    # Final summary
    elapsed = time.time() - start_time
    print("\n" + "=" * 60)
    print("GENERATION COMPLETE")
    print("=" * 60)
    print(f"✓ Successful: {successful}")
    print(f"✗ Failed: {failed}")
    print(f"⏱  Total time: {elapsed/60:.1f} minutes")
    print(f"📊 Average rate: {successful/elapsed:.2f} profiles/sec")
    print(f"📁 Output directory: {output_dir}")
    print("=" * 60)

    if failed > 0:
        print(f"\n⚠️  {failed} profiles failed to generate. Rerun the script to retry.")
        sys.exit(1)
    else:
        print("\n✓ All profiles generated successfully!")
        sys.exit(0)


if __name__ == "__main__":
    main()
