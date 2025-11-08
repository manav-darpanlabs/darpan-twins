#!/usr/bin/env python3
"""
Validate synthetic datasets for quality, distributions, and independence.
Generates comprehensive statistics report.
"""

import argparse
import json
import os
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
import numpy as np


def load_dataset(path: str) -> pd.DataFrame:
    """Load a CSV dataset."""
    print(f"Loading {path}...")
    df = pd.DataFrame(pd.read_csv(path))
    print(f"  ✓ Loaded {len(df):,} rows, {len(df.columns)} columns")
    return df


def check_user_overlap(train_df: pd.DataFrame, test_df: pd.DataFrame) -> Dict[str, Any]:
    """Check if there's any user overlap between train and test sets."""
    print("\n" + "="*60)
    print("CHECKING USER OVERLAP")
    print("="*60)

    train_users = set(train_df['user_id'].unique())
    test_users = set(test_df['user_id'].unique())
    overlap = train_users.intersection(test_users)

    result = {
        "train_unique_users": len(train_users),
        "test_unique_users": len(test_users),
        "overlap_count": len(overlap),
        "overlap_users": sorted(list(overlap)) if overlap else [],
        "is_valid": bool(len(overlap) == 0)
    }

    if result["is_valid"]:
        print(f"✓ No user overlap - datasets are independent")
        print(f"  Training users: {result['train_unique_users']}")
        print(f"  Test users: {result['test_unique_users']}")
    else:
        print(f"✗ WARNING: {len(overlap)} users appear in both datasets!")
        print(f"  Overlapping users: {overlap}")

    return result


def check_class_balance(df: pd.DataFrame, dataset_name: str) -> Dict[str, Any]:
    """Check if action classes are balanced."""
    print("\n" + "="*60)
    print(f"CLASS BALANCE - {dataset_name}")
    print("="*60)

    action_counts = df['action'].value_counts()
    total = len(df)

    result = {
        "action_A_count": int(action_counts.get('A', 0)),
        "action_B_count": int(action_counts.get('B', 0)),
        "action_A_pct": float(action_counts.get('A', 0) / total * 100),
        "action_B_pct": float(action_counts.get('B', 0) / total * 100),
        "is_balanced": bool(abs(action_counts.get('A', 0) / total - 0.5) < 0.05)  # Within 5% of 50%
    }

    print(f"  Action A: {result['action_A_count']:,} ({result['action_A_pct']:.1f}%)")
    print(f"  Action B: {result['action_B_count']:,} ({result['action_B_pct']:.1f}%)")

    if result["is_balanced"]:
        print(f"✓ Classes are balanced (within 5% of 50/50)")
    else:
        print(f"⚠ Classes are imbalanced (more than 5% deviation)")

    return result


def analyze_distributions(df: pd.DataFrame, dataset_name: str) -> Dict[str, Any]:
    """Analyze distributions of key variables."""
    print("\n" + "="*60)
    print(f"DISTRIBUTION ANALYSIS - {dataset_name}")
    print("="*60)

    result = {}

    # Demographics
    print("\n📊 DEMOGRAPHICS:")

    # Age distribution
    age_stats = {
        "mean": float(df['dem_age'].mean()),
        "std": float(df['dem_age'].std()),
        "min": int(df['dem_age'].min()),
        "max": int(df['dem_age'].max()),
        "median": float(df['dem_age'].median())
    }
    result["age"] = age_stats
    print(f"  Age: μ={age_stats['mean']:.1f}, σ={age_stats['std']:.1f}, "
          f"range=[{age_stats['min']}, {age_stats['max']}]")

    # Gender distribution
    gender_counts = {
        "male": int(df['dem_gender_male'].sum()),
        "female": int(df['dem_gender_female'].sum()),
        "other": int(df['dem_gender_other'].sum())
    }
    total_rows = len(df)
    gender_pcts = {k: v / total_rows * 100 for k, v in gender_counts.items()}
    result["gender"] = {"counts": gender_counts, "percentages": gender_pcts}
    print(f"  Gender: Male={gender_pcts['male']:.1f}%, "
          f"Female={gender_pcts['female']:.1f}%, Other={gender_pcts['other']:.1f}%")

    # Income distribution
    income_stats = {
        "mean": float(df['dem_income'].mean()),
        "std": float(df['dem_income'].std()),
        "median": float(df['dem_income'].median()),
        "min": float(df['dem_income'].min()),
        "max": float(df['dem_income'].max())
    }
    result["income"] = income_stats
    print(f"  Income: μ=₹{income_stats['mean']:,.0f}, median=₹{income_stats['median']:,.0f}")

    # OCEAN traits
    print("\n🧠 OCEAN TRAITS:")
    ocean_traits = ['ctx_openness', 'ctx_conscientiousness', 'ctx_extraversion',
                    'ctx_agreeableness', 'ctx_neuroticism']
    result["ocean"] = {}
    for trait in ocean_traits:
        trait_stats = {
            "mean": float(df[trait].mean()),
            "std": float(df[trait].std()),
            "min": float(df[trait].min()),
            "max": float(df[trait].max())
        }
        result["ocean"][trait] = trait_stats
        trait_name = trait.replace('ctx_', '').capitalize()
        print(f"  {trait_name:16s}: μ={trait_stats['mean']:.3f}, σ={trait_stats['std']:.3f}")

    # Derived preferences
    print("\n🎯 DERIVED PREFERENCES:")
    prefs = ['ctx_novelty_seeking', 'ctx_budget_sensitivity',
             'ctx_distance_tolerance', 'ctx_rating_focus']
    result["preferences"] = {}
    for pref in prefs:
        pref_stats = {
            "mean": float(df[pref].mean()),
            "std": float(df[pref].std())
        }
        result["preferences"][pref] = pref_stats
        pref_name = pref.replace('ctx_', '').replace('_', ' ').title()
        print(f"  {pref_name:20s}: μ={pref_stats['mean']:.3f}, σ={pref_stats['std']:.3f}")

    # Context features
    print("\n🌤️ CONTEXT FEATURES:")

    # Hour of day
    hour_stats = {
        "mean": float(df['hour_of_day'].mean()),
        "min": int(df['hour_of_day'].min()),
        "max": int(df['hour_of_day'].max())
    }
    result["hour_of_day"] = hour_stats
    print(f"  Hour of day: μ={hour_stats['mean']:.1f}, range=[{hour_stats['min']}, {hour_stats['max']}]")

    # Weekend proportion
    weekend_pct = float(df['is_weekend'].mean() * 100)
    result["weekend_pct"] = weekend_pct
    print(f"  Weekend orders: {weekend_pct:.1f}%")

    # Temperature
    temp_stats = {
        "mean": float(df['temperature_c'].mean()),
        "std": float(df['temperature_c'].std())
    }
    result["temperature_c"] = temp_stats
    print(f"  Temperature: μ={temp_stats['mean']:.1f}°C, σ={temp_stats['std']:.1f}°C")

    # Weather code distribution
    weather_counts = df['weather_code'].value_counts()
    result["weather_codes"] = {str(k): int(v) for k, v in weather_counts.items()}
    print(f"  Weather codes: {len(weather_counts)} unique types")

    # Rationale labels
    print("\n💭 RATIONALE DISTRIBUTION:")
    rationale_counts = df['rationale_label'].value_counts()
    result["rationale_labels"] = {str(k): int(v) for k, v in rationale_counts.items()}
    for label, count in rationale_counts.head(6).items():
        pct = count / len(df) * 100
        print(f"  {label:12s}: {count:7,} ({pct:5.1f}%)")

    return result


def check_data_quality(df: pd.DataFrame, dataset_name: str) -> Dict[str, Any]:
    """Check for data quality issues."""
    print("\n" + "="*60)
    print(f"DATA QUALITY CHECKS - {dataset_name}")
    print("="*60)

    result = {
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "missing_values": {},
        "duplicate_rows": 0,
        "issues": []
    }

    # Check for missing values
    missing = df.isnull().sum()
    if missing.any():
        result["missing_values"] = {str(k): int(v) for k, v in missing[missing > 0].items()}
        print(f"⚠ Missing values found:")
        for col, count in result["missing_values"].items():
            print(f"    {col}: {count} missing")
        result["issues"].append("missing_values")
    else:
        print(f"✓ No missing values")

    # Check for duplicate rows
    duplicates = df.duplicated().sum()
    result["duplicate_rows"] = int(duplicates)
    if duplicates > 0:
        print(f"⚠ {duplicates} duplicate rows found")
        result["issues"].append("duplicate_rows")
    else:
        print(f"✓ No duplicate rows")

    # Check OCEAN trait ranges (should be 0-1)
    ocean_traits = ['ctx_openness', 'ctx_conscientiousness', 'ctx_extraversion',
                    'ctx_agreeableness', 'ctx_neuroticism']
    ocean_out_of_range = 0
    for trait in ocean_traits:
        out_of_range = ((df[trait] < 0) | (df[trait] > 1)).sum()
        ocean_out_of_range += out_of_range

    if ocean_out_of_range > 0:
        print(f"⚠ {ocean_out_of_range} OCEAN trait values out of [0,1] range")
        result["issues"].append("ocean_out_of_range")
    else:
        print(f"✓ All OCEAN traits in valid [0,1] range")

    # Check for negative values in features that should be positive
    positive_features = ['dem_age', 'dem_income', 'diff_dish_price', 'diff_delivery_time_min']
    for feat in positive_features:
        if feat in df.columns:
            negative_count = (df[feat] < 0).sum()
            if negative_count > 0 and feat not in ['diff_dish_price', 'diff_delivery_time_min']:
                # diff features can be negative (that's the point)
                print(f"⚠ {negative_count} negative values in {feat}")
                result["issues"].append(f"negative_{feat}")

    if not result["issues"]:
        print(f"\n✓ All quality checks passed!")
    else:
        print(f"\n⚠ Found {len(result['issues'])} quality issues")

    return result


def compare_datasets(train_result: Dict, test_result: Dict) -> Dict[str, Any]:
    """Compare distributions between train and test sets."""
    print("\n" + "="*60)
    print("TRAIN vs TEST COMPARISON")
    print("="*60)

    comparison = {
        "age_diff": float(abs(train_result['age']['mean'] - test_result['age']['mean'])),
        "income_diff_pct": float(abs(train_result['income']['mean'] - test_result['income']['mean']) / train_result['income']['mean'] * 100),
        "ocean_trait_diffs": {},
        "is_similar": True
    }

    print("\n📊 DEMOGRAPHIC DIFFERENCES:")
    print(f"  Age difference: {comparison['age_diff']:.2f} years")
    print(f"  Income difference: {comparison['income_diff_pct']:.1f}%")

    print("\n🧠 OCEAN TRAIT DIFFERENCES:")
    for trait in train_result['ocean'].keys():
        diff = abs(train_result['ocean'][trait]['mean'] - test_result['ocean'][trait]['mean'])
        comparison['ocean_trait_diffs'][trait] = float(diff)
        trait_name = trait.replace('ctx_', '').capitalize()
        print(f"  {trait_name:16s}: {diff:.4f}")

    # Check if distributions are too different (warning threshold)
    if comparison['age_diff'] > 5:
        print(f"\n⚠ Age distributions differ by more than 5 years")
        comparison['is_similar'] = False
    if comparison['income_diff_pct'] > 20:
        print(f"\n⚠ Income distributions differ by more than 20%")
        comparison['is_similar'] = False

    if comparison['is_similar']:
        print(f"\n✓ Train and test distributions are similar")

    return comparison


def generate_summary_report(
    train_quality: Dict,
    test_quality: Dict,
    train_dist: Dict,
    test_dist: Dict,
    train_balance: Dict,
    test_balance: Dict,
    overlap: Dict,
    comparison: Dict
) -> Dict[str, Any]:
    """Generate comprehensive summary report."""

    report = {
        "summary": {
            "train_rows": train_quality['total_rows'],
            "test_rows": test_quality['total_rows'],
            "total_rows": train_quality['total_rows'] + test_quality['total_rows'],
            "train_users": overlap['train_unique_users'],
            "test_users": overlap['test_unique_users'],
            "total_users": overlap['train_unique_users'] + overlap['test_unique_users'],
            "user_overlap": overlap['overlap_count'],
            "datasets_independent": overlap['is_valid']
        },
        "data_quality": {
            "train": train_quality,
            "test": test_quality
        },
        "distributions": {
            "train": train_dist,
            "test": test_dist
        },
        "class_balance": {
            "train": train_balance,
            "test": test_balance
        },
        "comparison": comparison,
        "validation_status": {
            "user_independence": overlap['is_valid'],
            "train_quality_ok": len(train_quality['issues']) == 0,
            "test_quality_ok": len(test_quality['issues']) == 0,
            "train_balanced": train_balance['is_balanced'],
            "test_balanced": test_balance['is_balanced'],
            "distributions_similar": comparison['is_similar']
        }
    }

    # Overall validation status
    all_checks = [
        report['validation_status']['user_independence'],
        report['validation_status']['train_quality_ok'],
        report['validation_status']['test_quality_ok'],
        report['validation_status']['train_balanced'],
        report['validation_status']['test_balanced']
    ]
    report['validation_status']['all_checks_passed'] = all(all_checks)

    return report


def main():
    parser = argparse.ArgumentParser(description="Validate synthetic datasets")
    parser.add_argument("--train", type=str, default="data/train_expanded.csv",
                        help="Path to training dataset CSV")
    parser.add_argument("--test", type=str, default="data/test_expanded.csv",
                        help="Path to test dataset CSV")
    parser.add_argument("--output", type=str, default="data/validation_report.json",
                        help="Path to output validation report JSON")

    args = parser.parse_args()

    print("\n" + "="*60)
    print("DATASET VALIDATION")
    print("="*60)
    print(f"Training dataset: {args.train}")
    print(f"Test dataset: {args.test}")
    print("="*60)

    # Load datasets
    train_df = load_dataset(args.train)
    test_df = load_dataset(args.test)

    # Run validation checks
    overlap = check_user_overlap(train_df, test_df)
    train_balance = check_class_balance(train_df, "TRAINING")
    test_balance = check_class_balance(test_df, "TEST")
    train_quality = check_data_quality(train_df, "TRAINING")
    test_quality = check_data_quality(test_df, "TEST")
    train_dist = analyze_distributions(train_df, "TRAINING")
    test_dist = analyze_distributions(test_df, "TEST")
    comparison = compare_datasets(train_dist, test_dist)

    # Generate comprehensive report
    report = generate_summary_report(
        train_quality, test_quality,
        train_dist, test_dist,
        train_balance, test_balance,
        overlap, comparison
    )

    # Save report
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    # Print final summary
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)
    print(f"✓ Total rows generated: {report['summary']['total_rows']:,}")
    print(f"✓ Total unique users: {report['summary']['total_users']}")
    print(f"  - Training: {report['summary']['train_users']} users, {report['summary']['train_rows']:,} rows")
    print(f"  - Test: {report['summary']['test_users']} users, {report['summary']['test_rows']:,} rows")
    print()

    status = report['validation_status']
    checks = [
        ("User independence", status['user_independence']),
        ("Training data quality", status['train_quality_ok']),
        ("Test data quality", status['test_quality_ok']),
        ("Training class balance", status['train_balanced']),
        ("Test class balance", status['test_balanced']),
        ("Distribution similarity", status['distributions_similar'])
    ]

    for check_name, passed in checks:
        symbol = "✓" if passed else "✗"
        print(f"{symbol} {check_name}")

    print()
    if status['all_checks_passed']:
        print("🎉 ALL VALIDATION CHECKS PASSED!")
    else:
        print("⚠️  Some validation checks failed. Review the report for details.")

    print(f"\n📄 Detailed report saved to: {output_path}")
    print("="*60)

    return 0 if status['all_checks_passed'] else 1


if __name__ == "__main__":
    exit(main())
