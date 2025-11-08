import argparse
import json
import os
from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd


CUISINES = ["italian", "mexican", "sushi", "indian", "american", "chinese", "thai", "pizza", "burgers"]
RESTAURANT_NAMES = [
    "Spice Route", "Urban Fork", "Saffron & Co", "Basilico", "Tokyo Bites", "Bombay Bowl", "Taco Loco",
    "Sushi Hub", "Dragon Wok", "Mama Mia Pizza", "Burger Yard", "Curry Leaf", "Casa Mexicana", "Noodle House",
]
WEATHER_CODES = ["clear", "cloudy", "rain", "storm", "snow", "hot", "cold"]


@dataclass
class UserProfile:
    user_id: str
    openness: float
    conscientiousness: float
    extraversion: float
    agreeableness: float
    neuroticism: float
    # demographics
    age: int
    gender: str  # 'male'|'female'|'other'
    income: float  # monthly INR
    place_of_birth_avg_income: float
    place_of_birth_food_variety_index: float

    @staticmethod
    def from_json(path: str) -> "UserProfile":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        traits = data.get("OCEAN", {})
        # Demographics (optional in JSON)
        demo = data.get("demographics", {})
        age = int(demo.get("age", int(np.random.default_rng().integers(18, 65))))
        gender = str(demo.get("gender", np.random.default_rng().choice(["male", "female", "other"], p=[0.49, 0.49, 0.02])))
        # Annual INR incomes for Indian users (skewed, positive)
        income_default = float(
            np.clip(
                np.random.default_rng().lognormal(mean=np.log(600000.0), sigma=0.6),
                100000.0,
                5000000.0,
            )
        )
        pob_income_default = float(
            np.clip(
                np.random.default_rng().lognormal(mean=np.log(300000.0), sigma=0.6),
                50000.0,
                2000000.0,
            )
        )
        income = float(demo.get("income", income_default))
        pob_income = float(demo.get("place_of_birth_avg_income", pob_income_default))
        pob_variety = float(
            demo.get(
                "place_of_birth_food_variety_index",
                float(np.clip(np.random.default_rng().normal(0.6, 0.2), 0.0, 1.0)),
            )
        )

        return UserProfile(
            user_id=data.get("user_id", os.path.splitext(os.path.basename(path))[0]),
            openness=float(traits.get("openness", 0.5)),
            conscientiousness=float(traits.get("conscientiousness", 0.5)),
            extraversion=float(traits.get("extraversion", 0.5)),
            agreeableness=float(traits.get("agreeableness", 0.5)),
            neuroticism=float(traits.get("neuroticism", 0.5)),
            age=age,
            gender=gender,
            income=max(10000.0, income),
            place_of_birth_avg_income=max(5000.0, pob_income),
            place_of_birth_food_variety_index=float(pob_variety),
        )

    def derived_preferences(self) -> Dict[str, float]:
        novelty_seeking = _clip01((self.openness * 0.7) + (1 - self.conscientiousness) * 0.3)
        # Demographics influence: higher annual income -> lower budget sensitivity
        income_norm = np.tanh((self.income - 600000.0) / 600000.0)  # ~[-1, 1]
        budget_sensitivity = _clip01((1 - self.conscientiousness) * 0.4 + self.neuroticism * 0.4 - 0.4 * income_norm)
        distance_tolerance = _clip01((self.extraversion * 0.6) + self.openness * 0.2 - self.neuroticism * 0.3)
        rating_focus = _clip01((self.agreeableness * 0.4) + self.conscientiousness * 0.6)
        return {
            "novelty_seeking": novelty_seeking,
            "budget_sensitivity": budget_sensitivity,
            "distance_tolerance": distance_tolerance,
            "rating_focus": rating_focus,
        }


def _clip01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


def sample_context(rng: np.random.Generator) -> Dict[str, float]:
    hour = int(rng.integers(7, 24))  # 7am–11pm
    is_weekend = int(rng.random() < 0.3)
    temperature_c = float(np.round(rng.normal(24.0, 6.0), 1))
    precip_mm = float(np.round(max(0.0, rng.normal(1.0, 2.0)), 1))
    weather_code = rng.choice(WEATHER_CODES, p=[0.35, 0.2, 0.2, 0.05, 0.05, 0.1, 0.05])
    return {
        "hour_of_day": hour,
        "is_weekend": is_weekend,
        "temperature_c": temperature_c,
        "precip_mm": precip_mm,
        "weather_code": weather_code,
    }


def sample_card(rng: np.random.Generator) -> Dict[str, object]:
    cuisine = rng.choice(CUISINES)
    name = f"{rng.choice(RESTAURANT_NAMES)} — {cuisine.title()}"

    # Prices in INR (rupees), cuisine-dependent typical dish price
    base_price = {
        "sushi": 450.0, "indian": 220.0, "mexican": 250.0, "italian": 300.0, "american": 280.0,
        "chinese": 230.0, "thai": 270.0, "pizza": 240.0, "burgers": 200.0,
    }.get(cuisine, 250.0)
    dish_price = float(np.round(np.clip(rng.normal(base_price, 60.0), 50.0, 1000.0), 0))

    delivery_time_min = int(max(10, rng.normal(35, 10)))
    distance_km = float(np.round(max(0.2, rng.normal(3.0, 1.5)), 2))
    delivery_fee = float(np.round(np.clip(rng.normal(25.0, 15.0), 0.0, 150.0), 0))
    rating_avg = float(np.round(min(5.0, max(3.0, rng.normal(4.2, 0.4))), 1))
    num_reviews = int(np.clip(int(rng.lognormal(mean=4.0, sigma=1.0)), 5, 1000))
    coupon_prob = 0.25
    coupon_text = "SAVE20" if rng.random() < coupon_prob else ""
    friend_endorsements_count = int(rng.poisson(1.5))
    sponsored = 1.0 if rng.random() < 0.12 else 0.0

    features: Dict[str, object] = {
        "name": name,
        "friend_endorsements_count": friend_endorsements_count,
        "dish_price": dish_price,
        "delivery_time_min": delivery_time_min,
        "distance_km": distance_km,
        "delivery_fee": delivery_fee,
        "rating_avg": rating_avg,
        "num_reviews": num_reviews,
        "coupon_text": coupon_text,
        "cuisine": cuisine,
        "sponsored": sponsored,
    }

    for c in CUISINES:
        features[f"cuisine_{c}"] = 1.0 if c == cuisine else 0.0
    features["coupon_available"] = 1.0 if coupon_text else 0.0

    # Popularity proxy from endorsements + reviews
    # popularity removed per product decision

    return features


def context_adjustments(card: Dict[str, object], user_prefs: Dict[str, float], ctx: Dict[str, float]) -> float:
    # Positive score favors choosing this card
    score = 0.0

    # Weather / rain: prefer closer, faster, cheaper delivery, coupons
    if ctx["weather_code"] in ("rain", "storm") or ctx["precip_mm"] > 2.0:
        score += (-0.6) * float(card["distance_km"]) + (-0.4) * float(card["delivery_fee"]) + (-0.3) * float(card["delivery_time_min"]) + (0.5) * float(card["coupon_available"])  # type: ignore

    # Hot or very warm weather: slight bias to lighter cuisines
    if ctx["temperature_c"] >= 30:
        score += 0.3 * (float(card.get("cuisine_sushi", 0.0)) + float(card.get("cuisine_thai", 0.0)))  # type: ignore

    # Weekend: more novelty
    if int(ctx["is_weekend"]) == 1:
        score += 0.5 * (user_prefs["novelty_seeking"] - 0.5)

    # Late night: strong bias to closer/faster/cheaper
    if ctx["hour_of_day"] >= 22 or ctx["hour_of_day"] <= 8:
        score += (-0.5) * float(card["distance_km"]) + (-0.4) * float(card["delivery_time_min"]) + (-0.4) * float(card["dish_price"])  # type: ignore

    # Sponsored small visibility bump (not too large)
    score += 0.15 * float(card["sponsored"])  # type: ignore

    return score


def base_utility(card: Dict[str, object], user_prefs: Dict[str, float]) -> float:
    # Core tradeoffs independent of time/weather
    w_price = -0.8  # higher dish price is worse
    w_deliv_time = -0.6
    w_distance = -0.7
    w_fee = -0.6
    w_rating = 1.1
    w_reviews = 0.15
    w_coupon = 0.7

    price_term = w_price * float(card["dish_price"])  # type: ignore
    deliv_term = w_deliv_time * float(card["delivery_time_min"])  # type: ignore
    dist_term = w_distance * float(card["distance_km"])  # type: ignore
    fee_term = w_fee * float(card["delivery_fee"])  # type: ignore
    rating_term = w_rating * float(card["rating_avg"])  # type: ignore
    reviews_term = w_reviews * np.log1p(float(card["num_reviews"]))  # type: ignore
    coupon_term = w_coupon * float(card["coupon_available"])  # type: ignore
    pop_term = 0.0

    # Personality interactions
    budget_bonus = (user_prefs["budget_sensitivity"] - 0.5) * (-0.6 * float(card["dish_price"]) - 0.4 * float(card["delivery_fee"]) + 0.6 * float(card["coupon_available"]))  # type: ignore
    distance_penalty = (0.5 - user_prefs["distance_tolerance"]) * 0.9 * float(card["distance_km"])  # type: ignore
    rating_bonus = (user_prefs["rating_focus"]) * 0.5 * (float(card["rating_avg"]) - 4.0)  # type: ignore

    return float(
        price_term
        + deliv_term
        + dist_term
        + fee_term
        + rating_term
        + reviews_term
        + coupon_term
        + pop_term
        + budget_bonus
        - distance_penalty
        + rating_bonus
    )


def compute_utility(card: Dict[str, object], user_prefs: Dict[str, float], ctx: Dict[str, float]) -> float:
    return base_utility(card, user_prefs) + context_adjustments(card, user_prefs, ctx)


def to_diff_features(card_a: Dict[str, object], card_b: Dict[str, object]) -> Dict[str, float]:
    keys = [
        "dish_price",
        "delivery_time_min",
        "distance_km",
        "delivery_fee",
        "rating_avg",
        "num_reviews",
        "coupon_available",
        "sponsored",
        *[f"cuisine_{c}" for c in CUISINES],
    ]
    diff: Dict[str, float] = {}
    for key in keys:
        diff[f"diff_{key}"] = float(float(card_a.get(key, 0.0)) - float(card_b.get(key, 0.0)))
    return diff


def pick_rationale_label(chosen: Dict[str, object], other: Dict[str, object], user_prefs: Dict[str, float]) -> str:
    # Score rationale categories aligned with rationale_bank keys
    scores: Dict[str, float] = {}
    # rating advantage
    scores["rating"] = float(chosen.get("rating_avg", 0.0)) - float(other.get("rating_avg", 0.0))
    # eta (lower delivery time is better)
    scores["eta"] = float(other.get("delivery_time_min", 0.0)) - float(chosen.get("delivery_time_min", 0.0))
    # discount presence
    scores["discount"] = float(chosen.get("coupon_available", 0.0)) - float(other.get("coupon_available", 0.0))
    # popular (more reviews)
    scores["popular"] = float(chosen.get("num_reviews", 0.0)) - float(other.get("num_reviews", 0.0))
    # sponsored: prefer organic (chosen not sponsored vs other sponsored)
    scores["sponsored"] = float(other.get("sponsored", 0.0)) - float(chosen.get("sponsored", 0.0))
    # for_you: fallback based on novelty/rating focus and small gaps
    gap = abs(scores["rating"]) + abs(scores["eta"]) + abs(scores["discount"]) + abs(scores["popular"]) + abs(scores["sponsored"])  # type: ignore
    scores["for_you"] = 0.1 * (user_prefs.get("novelty_seeking", 0.5) + user_prefs.get("rating_focus", 0.5)) - 0.05 * gap

    # pick best key
    label = max(scores.items(), key=lambda kv: kv[1])[0]
    return label


def make_row(
    user: UserProfile,
    rng: np.random.Generator,
    t: int,
) -> Dict[str, object]:
    user_prefs = user.derived_preferences()
    ctx = sample_context(rng)

    card_a = sample_card(rng)
    card_b = sample_card(rng)

    util_a = compute_utility(card_a, user_prefs, ctx)
    util_b = compute_utility(card_b, user_prefs, ctx)

    logits = np.array([util_a, util_b])
    probs = np.exp(logits - np.max(logits))
    probs = probs / probs.sum()

    action_idx = int(rng.choice([0, 1], p=probs))
    action = "A" if action_idx == 0 else "B"

    reward_prob = float(1 / (1 + np.exp(-logits[action_idx] / 2)))
    reward = float(rng.random() < reward_prob)

    diff = to_diff_features(card_a, card_b)

    chosen = card_a if action == "A" else card_b
    other = card_b if action == "A" else card_a
    rationale_label = pick_rationale_label(chosen, other, user_prefs)

    row: Dict[str, object] = {
        "user_id": user.user_id,
        "t": t,
        "action": action,
        "reward": reward,
        "rationale_label": rationale_label,
        # context
        "hour_of_day": ctx["hour_of_day"],
        "is_weekend": ctx["is_weekend"],
        "temperature_c": ctx["temperature_c"],
        "precip_mm": ctx["precip_mm"],
        "weather_code": ctx["weather_code"],
        # personality
        "ctx_openness": user.openness,
        "ctx_conscientiousness": user.conscientiousness,
        "ctx_extraversion": user.extraversion,
        "ctx_agreeableness": user.agreeableness,
        "ctx_neuroticism": user.neuroticism,
        "ctx_novelty_seeking": user_prefs["novelty_seeking"],
        "ctx_budget_sensitivity": user_prefs["budget_sensitivity"],
        "ctx_distance_tolerance": user_prefs["distance_tolerance"],
        "ctx_rating_focus": user_prefs["rating_focus"],
        # demographics
        "dem_age": int(user.age),
        "dem_income": float(user.income),
        "dem_pob_avg_income": float(user.place_of_birth_avg_income),
        "dem_pob_food_variety_index": float(user.place_of_birth_food_variety_index),
        "dem_gender_male": 1.0 if user.gender == "male" else 0.0,
        "dem_gender_female": 1.0 if user.gender == "female" else 0.0,
        "dem_gender_other": 1.0 if user.gender not in ("male", "female") else 0.0,
    }

    row.update(diff)

    # optional: keep minimal display snapshot (names only)
    row.update({
        "A_name": card_a["name"],
        "B_name": card_b["name"],
    })

    return row


def load_profiles(profile_dir: str, user_range: str = None) -> List[UserProfile]:
    """
    Load user profiles from JSON files.

    Args:
        profile_dir: Directory containing user profile JSON files
        user_range: Optional range filter in format "USER_001:USER_500" (inclusive)

    Returns:
        List of UserProfile objects
    """
    profiles: List[UserProfile] = []

    # Parse user_range if provided
    start_user = None
    end_user = None
    if user_range:
        try:
            parts = user_range.split(":")
            if len(parts) == 2:
                start_user = parts[0].strip()
                end_user = parts[1].strip()
        except Exception:
            print(f"Warning: Invalid user_range format '{user_range}'. Expected format: 'USER_001:USER_500'")

    if os.path.isdir(profile_dir):
        for fname in sorted(os.listdir(profile_dir)):
            if not fname.endswith(".json"):
                continue

            # Extract user_id from filename (e.g., "USER_001.json" -> "USER_001")
            user_id = os.path.splitext(fname)[0]

            # Filter by user_range if specified
            if start_user and end_user:
                if not (start_user <= user_id <= end_user):
                    continue

            try:
                profiles.append(UserProfile.from_json(os.path.join(profile_dir, fname)))
            except Exception as e:
                print(f"Warning: Failed to load {fname}: {e}")
                continue

    if not profiles:
        print("Warning: No profiles loaded. Using default profile.")
        profiles = [
            UserProfile(
                user_id="USER_DEFAULT",
                openness=0.55,
                conscientiousness=0.55,
                extraversion=0.5,
                agreeableness=0.6,
                neuroticism=0.45,
                age=30,
                gender="male",
                income=600000.0,
                place_of_birth_avg_income=300000.0,
                place_of_birth_food_variety_index=0.6,
            )
        ]
    return profiles


def run(output_path: str, interactions_per_user: int, seed: int, profile_dir: str, user_range: str = None) -> pd.DataFrame:
    """
    Generate synthetic interaction data for users.

    Args:
        output_path: Path to output CSV file
        interactions_per_user: Number of interactions to generate per user
        seed: Random seed for reproducibility
        profile_dir: Directory containing user profile JSON files
        user_range: Optional range filter in format "USER_001:USER_500"

    Returns:
        DataFrame with generated interaction data
    """
    import time
    rng = np.random.default_rng(seed)
    profiles = load_profiles(profile_dir, user_range=user_range)

    print(f"\nGenerating synthetic data...")
    print(f"Users: {len(profiles)} ({profiles[0].user_id} to {profiles[-1].user_id})")
    print(f"Interactions per user: {interactions_per_user}")
    print(f"Total rows: {len(profiles) * interactions_per_user:,}")
    print(f"Random seed: {seed}")
    print("-" * 60)

    rows: List[Dict[str, object]] = []
    start_time = time.time()

    for idx, profile in enumerate(profiles):
        for t in range(interactions_per_user):
            rows.append(make_row(profile, rng, t))

        # Progress update every 10 users
        if (idx + 1) % 10 == 0 or idx == len(profiles) - 1:
            elapsed = time.time() - start_time
            rate = len(rows) / elapsed if elapsed > 0 else 0
            progress_pct = (idx + 1) / len(profiles) * 100
            rows_generated = len(rows)
            print(f"✓ {profile.user_id} - Progress: {idx + 1}/{len(profiles)} users "
                  f"({progress_pct:.1f}%) | {rows_generated:,} rows | "
                  f"Rate: {rate:.0f} rows/sec")

    print("\nBuilding DataFrame...")
    df = pd.DataFrame(rows)

    print(f"Saving to {output_path}...")
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    df.to_csv(output_path, index=False)

    elapsed = time.time() - start_time
    print("\n" + "=" * 60)
    print("GENERATION COMPLETE")
    print("=" * 60)
    print(f"✓ Total rows: {len(df):,}")
    print(f"✓ Total users: {len(profiles)}")
    print(f"⏱  Time: {elapsed/60:.1f} minutes ({elapsed:.1f} seconds)")
    print(f"📊 Rate: {len(df)/elapsed:.0f} rows/sec")
    print(f"📁 Output: {output_path}")
    print(f"💾 File size: {os.path.getsize(output_path) / 1024 / 1024:.1f} MB")
    print("=" * 60)

    return df


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic CAR data with time/weather and card schema diffs")
    parser.add_argument("--output", type=str, default="data/choices.csv", help="Output CSV file path")
    parser.add_argument("--profile_dir", type=str, default="data/twin_profiles", help="Directory containing user profile JSONs")
    parser.add_argument("--interactions_per_user", type=int, default=400, help="Number of interactions per user")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--user_range", type=str, default=None, help="User range filter (e.g., 'USER_001:USER_500')")

    args = parser.parse_args()
    run(
        output_path=args.output,
        interactions_per_user=args.interactions_per_user,
        seed=args.seed,
        profile_dir=args.profile_dir,
        user_range=args.user_range,
    )


if __name__ == "__main__":
    main()
