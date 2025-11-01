import base64
import json
import re
from typing import Any, Dict

from .tools import LLMClient


WHITELIST_FIELDS = [
    "name",
    "cuisine",
    "dish_price",
    "delivery_time_min",
    "distance_km",
    "delivery_fee",
    "rating_avg",
    "num_reviews",
    "coupon_text",
    "sponsored",
]


def validate_card(card: Dict[str, Any]) -> Dict[str, Any]:
    clean: Dict[str, Any] = {}
    for k in WHITELIST_FIELDS:
        if k in card:
            clean[k] = card[k]
    # Coerce types
    def ffloat(x: Any, d: float = 0.0) -> float:
        try:
            return float(x)
        except Exception:
            return d

    def fint(x: Any, d: int = 0) -> int:
        try:
            return int(float(x))
        except Exception:
            return d

    if "dish_price" in clean:
        clean["dish_price"] = ffloat(clean["dish_price"]) 
    if "delivery_time_min" in clean:
        clean["delivery_time_min"] = fint(clean["delivery_time_min"]) 
    if "distance_km" in clean:
        clean["distance_km"] = ffloat(clean["distance_km"]) 
    if "delivery_fee" in clean:
        clean["delivery_fee"] = ffloat(clean["delivery_fee"]) 
    if "rating_avg" in clean:
        clean["rating_avg"] = ffloat(clean["rating_avg"]) 
    if "num_reviews" in clean:
        clean["num_reviews"] = fint(clean["num_reviews"]) 
    if "sponsored" in clean:
        v = str(clean["sponsored"]).strip().lower()
        clean["sponsored"] = 1.0 if v in ("1", "true", "yes") else 0.0
    return clean


def build_vision_prompt() -> str:
    schema = {
        "name": "string",
        "cuisine": "string",
        "dish_price": "number",
        "delivery_time_min": "number",
        "distance_km": "number",
        "delivery_fee": "number",
        "rating_avg": "number",
        "num_reviews": "number",
        "coupon_text": "string",
        "sponsored": "0|1",
    }
    return (
        "Extract ONLY the following fields from the restaurant card image as strict JSON."
        " No extra keys, no text outside JSON."
        f" Schema: {json.dumps(schema)}"
    )


def extract_from_image(image_bytes: bytes) -> Dict[str, Any]:
    client = LLMClient()
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    prompt = build_vision_prompt()
    text = client.generate_vision(prompt, image_b64=b64, temperature=0.1, max_tokens=400)
    if not text:
        return {}
    # Try parse
    try:
        data = json.loads(text)
    except Exception:
        # Try to find JSON substring
        m = re.search(r"\{[\s\S]*\}\s*$", text.strip())
        try:
            data = json.loads(m.group(0)) if m else {}
        except Exception:
            return {}
    if not isinstance(data, dict):
        return {}
    return validate_card(data)


