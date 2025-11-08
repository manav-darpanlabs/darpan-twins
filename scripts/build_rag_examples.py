#!/usr/bin/env python3
"""
Build RAG example database from synthetic data.
Converts CSV rows into JSON format optimized for retrieval.

This script transforms the training data (generated via generate_synth.py)
into a RAG-ready format for LLM context injection.
"""

import pandas as pd
import json
import argparse
from pathlib import Path
from typing import Dict, List


def build_rag_examples(csv_path: str, output_path: str, max_examples: int = 10000, seed: int = 42):
    """
    Convert synthetic data CSV to RAG examples JSON.

    Args:
        csv_path: Path to synthetic data (e.g., train_expanded.csv)
        output_path: Path to output JSON file
        max_examples: Maximum examples to keep (default: 10,000)
        seed: Random seed for sampling
    """
    print(f"\n{'='*60}")
    print("BUILDING RAG EXAMPLE DATABASE")
    print(f"{'='*60}")
    print(f"Input: {csv_path}")
    print(f"Output: {output_path}")
    print(f"Max examples: {max_examples:,}")
    print(f"Random seed: {seed}")
    print(f"{'='*60}\n")

    # Load data
    print(f"Loading {csv_path}...")
    df = pd.read_csv(csv_path)
    print(f"✓ Loaded {len(df):,} rows\n")

    # Sample diverse examples
    print(f"Sampling {min(max_examples, len(df)):,} diverse examples...")
    sampled_df = df.sample(n=min(max_examples, len(df)), random_state=seed)

    examples = []
    total = len(sampled_df)

    for idx, (_, row) in enumerate(sampled_df.iterrows()):
        # Build example dict
        example = {
            "user_id": str(row['user_id']),
            "ocean": {
                "openness": float(row['ctx_openness']),
                "conscientiousness": float(row['ctx_conscientiousness']),
                "extraversion": float(row['ctx_extraversion']),
                "agreeableness": float(row['ctx_agreeableness']),
                "neuroticism": float(row['ctx_neuroticism'])
            },
            "demographics": {
                "age": int(row['dem_age']),
                "income": float(row['dem_income']),
                "gender": _get_gender(row),
                "place_of_birth_avg_income": float(row['dem_pob_avg_income']),
                "place_of_birth_food_variety_index": float(row['dem_pob_food_variety_index'])
            },
            "derived_preferences": {
                "novelty_seeking": float(row['ctx_novelty_seeking']),
                "budget_sensitivity": float(row['ctx_budget_sensitivity']),
                "distance_tolerance": float(row['ctx_distance_tolerance']),
                "rating_focus": float(row['ctx_rating_focus'])
            },
            "context": {
                "hour_of_day": int(row['hour_of_day']),
                "is_weekend": bool(row['is_weekend']),
                "temperature_c": float(row['temperature_c']),
                "precip_mm": float(row['precip_mm']),
                "weather_code": str(row['weather_code'])
            },
            "context_summary": _format_context_summary(row),
            "decision": {
                "action": str(row['action']),
                "rationale_category": str(row['rationale_label'])
            },
            "card_differences": {
                "rating_avg": float(row['diff_rating_avg']),
                "dish_price": float(row['diff_dish_price']),
                "delivery_time_min": float(row['diff_delivery_time_min']),
                "distance_km": float(row['diff_distance_km']),
                "delivery_fee": float(row['diff_delivery_fee']),
                "num_reviews": float(row['diff_num_reviews']),
                "coupon_available": float(row['diff_coupon_available']),
                "sponsored": float(row['diff_sponsored'])
            },
            "reasoning": _generate_reasoning(row)
        }

        examples.append(example)

        # Progress update
        if (idx + 1) % 1000 == 0 or idx == total - 1:
            print(f"  Processed {idx + 1:,}/{total:,} ({(idx+1)/total*100:.1f}%)")

    # Save to JSON
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"\nSaving to {output_path}...")
    with open(output_path, 'w') as f:
        json.dump(examples, f, indent=2)

    # Stats
    file_size_mb = output_path.stat().st_size / 1024 / 1024

    print(f"\n{'='*60}")
    print("RAG DATABASE CREATED")
    print(f"{'='*60}")
    print(f"✓ Total examples: {len(examples):,}")
    print(f"✓ Unique users: {len(set(ex['user_id'] for ex in examples)):,}")
    print(f"✓ File size: {file_size_mb:.1f} MB")
    print(f"✓ Avg example size: {file_size_mb*1024/len(examples):.1f} KB")
    print(f"📁 Saved to: {output_path}")
    print(f"{'='*60}\n")

    # Sample example
    print("Sample example (first entry):")
    print(json.dumps(examples[0], indent=2)[:500] + "...")
    print()


def _get_gender(row: pd.Series) -> str:
    """Extract gender from one-hot encoded columns."""
    if row['dem_gender_male'] == 1:
        return "male"
    elif row['dem_gender_female'] == 1:
        return "female"
    else:
        return "other"


def _format_context_summary(row: pd.Series) -> str:
    """Format context as human-readable string."""
    parts = []

    # Time
    hour = int(row['hour_of_day'])
    time_of_day = (
        "early morning" if 5 <= hour < 9 else
        "late morning" if 9 <= hour < 12 else
        "afternoon" if 12 <= hour < 17 else
        "evening" if 17 <= hour < 21 else
        "night"
    )
    parts.append(f"{hour}:00 ({time_of_day})")

    # Day
    if row['is_weekend']:
        parts.append("weekend")
    else:
        parts.append("weekday")

    # Weather
    temp = row['temperature_c']
    if temp >= 30:
        parts.append(f"hot {temp:.0f}°C")
    elif temp < 20:
        parts.append(f"cool {temp:.0f}°C")
    else:
        parts.append(f"{temp:.0f}°C")

    if row['precip_mm'] > 0:
        parts.append(f"rain {row['precip_mm']:.1f}mm")

    return ", ".join(parts)


def _generate_reasoning(row: pd.Series) -> str:
    """Generate human-readable reasoning for the decision."""
    action = row['action']
    category = row['rationale_label']

    # Build reasoning based on top drivers
    reasons = []

    if category == "rating":
        if row['diff_rating_avg'] > 0.3:
            reasons.append(f"Card {action} has significantly better rating ({row['diff_rating_avg']:.1f}⭐ higher)")
        else:
            reasons.append(f"Card {action} has better rating")

    elif category == "eta":
        if row['diff_delivery_time_min'] < -10:
            reasons.append(f"Card {action} is much faster ({abs(row['diff_delivery_time_min']):.0f} min quicker)")
        else:
            reasons.append(f"Card {action} has faster delivery")

    elif category == "discount":
        reasons.append(f"Card {action} has a coupon/discount available")

    elif category == "popular":
        if row['diff_num_reviews'] > 500:
            reasons.append(f"Card {action} is more popular ({abs(row['diff_num_reviews']):.0f} more reviews)")
        else:
            reasons.append(f"Card {action} has more reviews")

    elif category == "sponsored":
        reasons.append(f"Card {action} is organic (not sponsored)")

    elif category == "for_you":
        reasons.append(f"Card {action} aligns better with my preferences")

    # Add context-based reasoning
    if row['precip_mm'] > 2 and abs(row['diff_distance_km']) > 1:
        reasons.append("considering the rainy weather")

    if row['hour_of_day'] >= 22 and abs(row['diff_delivery_time_min']) > 5:
        reasons.append("given the late hour")

    # Add personality-based reasoning
    if row['ctx_budget_sensitivity'] > 0.7 and abs(row['diff_dish_price']) > 100:
        reasons.append("being budget-conscious")

    if row['ctx_novelty_seeking'] > 0.7:
        reasons.append("matching my adventurous nature")

    if not reasons:
        reasons.append(f"Card {action} seems like the better overall choice")

    return f"Chose {action}: {', '.join(reasons[:2])}"  # Limit to 2 main reasons


def main():
    parser = argparse.ArgumentParser(
        description="Build RAG example database from synthetic data CSV"
    )
    parser.add_argument(
        "--input",
        type=str,
        default="data/train_expanded.csv",
        help="Input CSV file with synthetic data"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/rag_examples.json",
        help="Output JSON file for RAG database"
    )
    parser.add_argument(
        "--max_examples",
        type=int,
        default=10000,
        help="Maximum number of examples to keep (default: 10,000)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for sampling (default: 42)"
    )

    args = parser.parse_args()

    build_rag_examples(
        csv_path=args.input,
        output_path=args.output,
        max_examples=args.max_examples,
        seed=args.seed
    )


if __name__ == "__main__":
    main()
