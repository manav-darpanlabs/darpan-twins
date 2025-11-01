from typing import List, Tuple, Dict
import json
import os
import random


_RATIONALE_BANK_CACHE: Dict[str, List[str]] = {}


def load_rationale_bank(path: str = os.path.join("data", "rationale_bank.json")) -> Dict[str, List[str]]:
    global _RATIONALE_BANK_CACHE
    if _RATIONALE_BANK_CACHE:
        return _RATIONALE_BANK_CACHE
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        _RATIONALE_BANK_CACHE = data.get("drivers", {})
    except Exception:
        _RATIONALE_BANK_CACHE = {}
    return _RATIONALE_BANK_CACHE


FEATURE_TO_BANK = {
    "diff_rating_avg": "rating",
    "diff_num_reviews": "popular",
    "diff_delivery_time_min": "eta",
    "diff_coupon_available": "discount",
    "diff_sponsored": "sponsored",
}


def pretty_feature(name: str) -> str:
    mapping = {
        "diff_rating_avg": "better rating",
        "diff_num_reviews": "more reviews",
        "diff_dish_price": "lower dish price",
        "diff_delivery_fee": "lower delivery fee",
        "diff_delivery_time_min": "faster delivery",
        "diff_distance_km": "closer distance",
        "diff_coupon_available": "has a coupon",
        "diff_sponsored": "sponsored placement",
    }
    if name.startswith("diff_cuisine_"):
        return f"cuisine fit ({name.replace('diff_cuisine_', '')})"
    return mapping.get(name, name)


def drivers_to_phrases(drivers: List[Tuple[str, float]], top_k: int = 3) -> List[str]:
    if not drivers:
        return ["overall looks better"]
    phrases: List[str] = []
    for feat, contrib in drivers[:top_k]:
        if contrib >= 0:
            phrases.append(pretty_feature(feat))
    if not phrases:
        phrases.append(pretty_feature(drivers[0][0]))
    return phrases


def build_llm_prompt(user_name: str, ocean: Dict[str, float], values_top3: List[str], context_summary: str, action: str, drivers: List[str]) -> str:
    return (
        "You are {name}'s digital twin.\n"
        "Traits (OCEAN): O={O:.2f}, C={C:.2f}, E={E:.2f}, A={A:.2f}, N={N:.2f}.\n"
        "You usually value: {values}.\n"
        "Current context: {ctx}.\n"
        "Predicted action: {action}.\n"
        "Drivers: {drivers}.\n"
        "Task: Write ONE short sentence about why this restaurant card is the better pick."
        " Mention 1–2 drivers above. Keep it under 20 words."
        " Stay strictly on the food/restaurant/delivery domain; avoid generic corporate language or unrelated topics."
    ).format(
        name=user_name,
        O=ocean.get("openness", 0.5),
        C=ocean.get("conscientiousness", 0.5),
        E=ocean.get("extraversion", 0.5),
        A=ocean.get("agreeableness", 0.5),
        N=ocean.get("neuroticism", 0.5),
        values=", ".join(values_top3) if values_top3 else "—",
        ctx=context_summary,
        action=action,
        drivers=", ".join(drivers),
    )


def fallback_rationale(action: str, driver_phrases: List[str]) -> str:
    bank = load_rationale_bank()
    # Try to map the first positive driver to a bank phrase
    chosen = None
    for phrase in driver_phrases:
        # reverse-map based on keywords in pretty_feature; best-effort
        key = None
        if "rating" in phrase:
            key = "rating"
        elif "delivery" in phrase or "faster" in phrase:
            key = "eta"
        elif "coupon" in phrase or "discount" in phrase:
            key = "discount"
        elif "sponsored" in phrase:
            key = "sponsored"
        elif "reviews" in phrase:
            key = "popular"
        if key and key in bank and bank[key]:
            chosen = random.choice(bank[key])
            break
    if not chosen:
        chosen = "This one looks a bit better overall."
    return f"I'd pick {action}. {chosen}"
