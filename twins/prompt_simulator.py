import json
import os
import re
from typing import Any, Dict, List, Tuple, Optional, Callable

import joblib
import numpy as np
import pandas as pd

from .twin_profile import TwinProfile
from .tools import LLMClient


def summarize_ctx(row: Dict[str, Any]) -> str:
    parts: List[str] = []
    hour = row.get("hour_of_day")
    if hour is not None:
        parts.append(f"{int(hour)}:00")
    if int(row.get("is_weekend", 0)) == 1:
        parts.append("weekend")
    t = row.get("temperature_c")
    if t is not None:
        parts.append(f"{float(t):.0f}°C")
    p = row.get("precip_mm")
    if p is not None and float(p) > 0:
        parts.append(f"rain {float(p):.1f}mm")
    return ", ".join(parts) if parts else "context"


def build_user_history(user_id: str, df: pd.DataFrame, k: int) -> List[str]:
    sub = df[df["user_id"].astype(str) == str(user_id)].tail(k)
    bullets: List[str] = []
    for _, r in sub.iterrows():
        ctx = summarize_ctx(r.to_dict())
        action = str(r.get("action", "A"))
        label = str(r.get("rationale_label", "")).strip()
        bullets.append(f"- {ctx} → chose {action}{(' (' + label + ')') if label else ''}")
    return bullets


def build_context_summary(runtime_context: Dict[str, Any]) -> str:
    return summarize_ctx(runtime_context)


def build_response_prompt(profile: TwinProfile, history_bullets: List[str], context_summary: str, user_id: str) -> str:
    style = profile.style_tokens()
    ocean = {
        "O": profile.openness,
        "C": profile.conscientiousness,
        "E": profile.extraversion,
        "A": profile.agreeableness,
        "N": profile.neuroticism,
    }
    hist = "\n".join(history_bullets) if history_bullets else "(no prior history)"
    return (
        "[SYSTEM] You are simulating a specific user's internal thinking. First-person, concise, truthful.\n"
        "Do NOT hallucinate. Only use the provided history and traits. If unsure, say you're unsure.\n"
        f"User identity token: <uid:{user_id}>. Never speak as any other user.\n"
        "[USER] Persona:\n"
        f"OCEAN: O={ocean['O']:.2f}, C={ocean['C']:.2f}, E={ocean['E']:.2f}, A={ocean['A']:.2f}, N={ocean['N']:.2f}.\n"
        f"Tone knobs: enthusiasm={style['enthusiasm']:.2f}, politeness={style['politeness']:.2f}, brevity={style['brevity']:.2f}.\n"
        "Recent history (most recent last):\n"
        f"{hist}\n"
        f"Current context: {context_summary}.\n"
        "Task: Write a brief first-person thought on this context (1–2 sentences)."
        " Do NOT include ratings or metadata; no Likert; no extraneous text."
    )


def build_likert_prompt(response_text: str) -> str:
    return (
        "Rate the sentiment of the following first-person thought on a Likert scale 1–5,"
        " where 1 is very negative, 3 is neutral, and 5 is very positive."
        " Respond with ONLY the integer 1, 2, 3, 4, or 5.\n\n"
        f"Text: {response_text}"
    )


class LikertScorer:
    def __init__(self, model_dir: str = "models", client: Optional[LLMClient] = None) -> None:
        self.path = os.path.join(model_dir, "likert_pipeline.pkl")
        self.pipe = None
        if os.path.exists(self.path):
            try:
                self.pipe = joblib.load(self.path)
            except Exception:
                self.pipe = None
        self.client = client

    @staticmethod
    def _parse_int(s: str) -> Optional[int]:
        if not isinstance(s, str):
            return None
        m = re.search(r"\b([1-5])\b", s)
        if not m:
            return None
        try:
            return int(m.group(1))
        except Exception:
            return None

    def score(self, text: str) -> int:
        if not text:
            return 3
        # Prefer LLM scoring when available
        if self.client is not None:
            prompt = build_likert_prompt(text)
            resp = self.client.generate(prompt)
            val = self._parse_int(resp)
            if isinstance(val, int):
                return int(np.clip(val, 1, 5))
        # Fallback to local pipeline if present
        if self.pipe is not None:
            try:
                pred = self.pipe.predict([text])[0]
                return int(np.clip(int(pred), 1, 5))
            except Exception:
                pass
        # Last-resort heuristic
        t = text.lower()
        positive = any(k in t for k in ["love", "great", "good", "like", "happy", "fast", "tasty", "awesome"]) 
        negative = any(k in t for k in ["hate", "bad", "slow", "expensive", "far", "wait", "cold", "bland"]) 
        if positive and not negative:
            return 4
        if negative and not positive:
            return 2
        return 3


def run_simulation_for_users(
    profile_paths: List[str],
    choices_csv: str,
    runtime_context: Dict[str, Any],
    k: int = 50,
) -> List[Dict[str, Any]]:
    df = pd.read_csv(choices_csv)
    client = LLMClient()
    scorer = LikertScorer(client=client)
    results: List[Dict[str, Any]] = []
    for path in profile_paths:
        profile = TwinProfile.from_json(path)
        history = build_user_history(profile.user_id, df, k)
        ctx_summary = build_context_summary(runtime_context)
        prompt = build_response_prompt(profile, history, ctx_summary, profile.user_id)
        response = client.generate(prompt)
        likert = scorer.score(response)
        results.append(
            {
                "user_id": profile.user_id,
                "name": getattr(profile, "name", profile.user_id),
                "response": response,
                "likert": likert,
                "prompt": prompt,
            }
        )
    return results



# ----------------------------- Dual LLM Chooser -----------------------------

def summarize_card(card: Dict[str, Any]) -> str:
    name = str(card.get("name", ""))
    cuisine = None
    for key, val in card.items():
        if key.startswith("cuisine_") and val == 1.0:
            cuisine = key.replace("cuisine_", "")
            break
    cuisine = cuisine or str(card.get("cuisine", ""))
    rating = card.get("rating_avg", "")
    eta = card.get("delivery_time_min", "")
    dist = card.get("distance_km", "")
    fee = card.get("delivery_fee", "")
    price = card.get("dish_price", "")
    coupon = "yes" if card.get("coupon_available", 0.0) else "no"
    sponsored = "yes" if card.get("sponsored", 0.0) else "no"
    return (
        f"{name} ({cuisine}) • rating {rating} • ETA {eta}m • {dist}km • "
        f"fee ₹{fee} • price ₹{price} • coupon {coupon} • sponsored {sponsored}"
    )


def build_responder_prompt(
    profile: TwinProfile,
    history_bullets: List[str],
    context_summary: str,
    user_id: str,
    card_summary: str,
) -> str:
    style = profile.style_tokens()
    ocean = {
        "O": profile.openness,
        "C": profile.conscientiousness,
        "E": profile.extraversion,
        "A": profile.agreeableness,
        "N": profile.neuroticism,
    }
    hist = "\n".join(history_bullets) if history_bullets else "(no prior history)"
    return (
        "[SYSTEM] You are simulating a specific user's internal thinking. First-person, concise, truthful.\n"
        "Do NOT hallucinate. Only use the provided history and traits. If unsure, say you're unsure.\n"
        f"User identity token: <uid:{user_id}>. Never speak as any other user.\n"
        "[USER] Persona:\n"
        f"OCEAN: O={ocean['O']:.2f}, C={ocean['C']:.2f}, E={ocean['E']:.2f}, A={ocean['A']:.2f}, N={ocean['N']:.2f}.\n"
        f"Tone: enthusiasm={style['enthusiasm']:.2f}, politeness={style['politeness']:.2f}, brevity={style['brevity']:.2f}.\n"
        "Recent history (most recent last):\n"
        f"{hist}\n"
        f"Current context: {context_summary}.\n"
        f"Card: {card_summary}.\n"
        "Task: Write a brief first-person thought on this card (1–2 sentences)."
        " No ratings, no metadata, no Likert."
    )


def build_judge_prompt(
    card_a_summary: str,
    card_b_summary: str,
    response_a: str,
    response_b: str,
    context_summary: str,
) -> str:
    return (
        "You are a careful judge. Compare two restaurant cards and two first-person thoughts.\n"
        f"Context: {context_summary}\n"
        f"Card A: {card_a_summary}\n"
        f"Card B: {card_b_summary}\n"
        f"Response A: {response_a}\n"
        f"Response B: {response_b}\n"
        "Pick strictly one: 'A' or 'B' based on which response better matches the card and context.\n"
        "Return STRICT JSON only: {\"action\": \"A|B\", \"reason\": \"one sentence\"}."
    )


def _parse_judge_json(text: str) -> Tuple[str, str]:
    try:
        data = json.loads(text)
        action = str(data.get("action", "")).upper()
        reason = str(data.get("reason", "")).strip()
        if action in ("A", "B") and reason:
            return action, reason
    except Exception:
        pass
    # Fallback: regex
    m = re.search(r"\b(\"action\"\s*:\s*\"?([AB])\"?)", text, flags=re.I)
    action = m.group(2).upper() if m else ""
    m2 = re.search(r"\"reason\"\s*:\s*\"([^\"]+)\"", text)
    reason = m2.group(1).strip() if m2 else ""
    if action not in ("A", "B"):
        # last resort: first letter mentioned
        m3 = re.search(r"\b([AB])\b", text, flags=re.I)
        action = m3.group(1).upper() if m3 else "A"
    if not reason:
        reason = "Better aligned with the response and context."
    return action, reason


WHITELIST_CARD_FIELDS = [
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


def to_whitelisted_json(card: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for k in WHITELIST_CARD_FIELDS:
        if k in card:
            out[k] = card[k]
    return out


def build_judge_prompt_grounded(
    profile_json: Dict[str, Any],
    history_bullets: List[str],
    scenario_json: Dict[str, Any],
    card_a_json: Dict[str, Any],
    card_b_json: Dict[str, Any],
) -> str:
    history = "\n".join(history_bullets) if history_bullets else "(no prior history)"
    schema = '{"choice":"A|B|tie","reasons":["…","…"],"checks":{"price":"A|B|tie","delivery":"A|B|tie","fit":"A|B|tie","trust":"A|B|tie"}}'
    return (
        "[SYSTEM] You are a careful evaluator. Pick the better card for THIS user and context."
        " Rules: Cite only fields provided. Return strict JSON (no prose)."\
        "\n[USER]\nPROFILE: {profile}\nPAST DATA:\n{history}\nSCENARIO: {scenario}\nCARD_A: {card_a}\nCARD_B: {card_b}\n"\
        "First compute rubric checks (price, delivery, cuisine fit, trust using rating+reviews+sponsored), then choose."
        " Do not invent fields. Return EXACTLY this JSON schema: {schema}"
    ).format(
        profile=json.dumps(profile_json, ensure_ascii=False),
        history=history,
        scenario=json.dumps(scenario_json, ensure_ascii=False),
        card_a=json.dumps(card_a_json, ensure_ascii=False),
        card_b=json.dumps(card_b_json, ensure_ascii=False),
        schema=schema,
    )


def call_judge_samples(
    client: LLMClient,
    profile_json: Dict[str, Any],
    history_bullets: List[str],
    scenario_json: Dict[str, Any],
    card_a_json: Dict[str, Any],
    card_b_json: Dict[str, Any],
    n: int = 3,
    temperature: float = 0.3,
) -> List[Dict[str, Any]]:
    prompt = build_judge_prompt_grounded(profile_json, history_bullets, scenario_json, card_a_json, card_b_json)
    outputs: List[Dict[str, Any]] = []
    for _ in range(max(1, n)):
        text = client.generate(prompt, temperature=temperature, max_tokens=220)
        try:
            data = json.loads(text)
            outputs.append(data)
        except Exception:
            # try to extract JSON substring
            m = re.search(r"\{[\s\S]*\}$", text.strip())
            if m:
                try:
                    outputs.append(json.loads(m.group(0)))
                except Exception:
                    pass
    return outputs


def agg_majority(choices: List[str]) -> str:
    if not choices:
        return "tie"
    counts: Dict[str, int] = {"A": 0, "B": 0, "tie": 0}
    for c in choices:
        if c in counts:
            counts[c] += 1
    best = max(counts.items(), key=lambda kv: kv[1])[0]
    if counts[best] == counts.get("tie", 0) and best != "tie":
        return "tie"
    return best


def aggregate_judge_samples(samples_ab: List[Dict[str, Any]], samples_ba: List[Dict[str, Any]]) -> Tuple[str, Dict[str, str], List[str]]:
    # Normalize BA order back to AB
    norm_samples: List[Dict[str, Any]] = []
    for s in samples_ab:
        norm_samples.append(s)
    for s in samples_ba:
        t = dict(s)
        ch = str(t.get("choice", "")).lower()
        if ch == "a":
            t["choice"] = "B"
        elif ch == "b":
            t["choice"] = "A"
        norm_samples.append(t)

    # Validate, coerce values to A/B/tie, keep checks keys only
    valid: List[Dict[str, Any]] = []
    for s in norm_samples:
        choice = str(s.get("choice", "")).upper()
        if choice not in ("A", "B", "TIE"):
            continue
        checks = s.get("checks", {}) or {}
        clean_checks = {}
        for k in ("price", "delivery", "fit", "trust"):
            v = str(checks.get(k, "tie")).lower()
            vv = "A" if v == "a" else ("B" if v == "b" else "tie")
            clean_checks[k] = vv
        reasons = s.get("reasons", []) or []
        reasons = [str(r).strip() for r in reasons if str(r).strip()]
        valid.append({"choice": "A" if choice == "A" else ("B" if choice == "B" else "tie"), "checks": clean_checks, "reasons": reasons[:3]})

    final_choice = agg_majority([v["choice"] for v in valid])
    # Aggregate checks by majority
    checks_final: Dict[str, str] = {}
    for k in ("price", "delivery", "fit", "trust"):
        checks_final[k] = agg_majority([v["checks"][k] for v in valid if k in v["checks"]])
    # Reasons: take most frequent 1–2
    reason_counts: Dict[str, int] = {}
    for v in valid:
        for r in v.get("reasons", []):
            reason_counts[r] = reason_counts.get(r, 0) + 1
    reasons_sorted = sorted(reason_counts.items(), key=lambda kv: kv[1], reverse=True)
    reasons_final = [r for r, _ in reasons_sorted[:2]] or ["better match on checked criteria"]
    return final_choice, checks_final, reasons_final


def run_dual_llm_for_users(
    profile_paths: List[str],
    choices_csv: str,
    runtime_context: Dict[str, Any],
    card_a: Dict[str, Any],
    card_b: Dict[str, Any],
    k: int = 50,
    n_samples: int = 3,
    temperature: float = 0.3,
    progress_cb: Optional[Callable[[int, int], None]] = None,
) -> List[Dict[str, Any]]:
    df = pd.read_csv(choices_csv)
    client = LLMClient()
    scorer = LikertScorer(client=client)
    results: List[Dict[str, Any]] = []
    a_sum = summarize_card(card_a)
    b_sum = summarize_card(card_b)
    ctx_summary = build_context_summary(runtime_context)
    scenario_json = {"context": ctx_summary}
    card_a_json = to_whitelisted_json(card_a)
    card_b_json = to_whitelisted_json(card_b)
    # progress tracking (exact): per user → 2 responder calls + 2*n_samples judge calls + 1 likert
    total_steps = max(1, len(profile_paths) * (2 + 2 * n_samples + 1))
    steps_done = 0

    def bump(delta: int = 1) -> None:
        nonlocal steps_done
        steps_done += delta
        if progress_cb is not None:
            progress_cb(min(steps_done, total_steps), total_steps)

    for path in profile_paths:
        profile = TwinProfile.from_json(path)
        history = build_user_history(profile.user_id, df, k)
        # Responder A/B
        prompt_a = build_responder_prompt(profile, history, ctx_summary, profile.user_id, a_sum)
        prompt_b = build_responder_prompt(profile, history, ctx_summary, profile.user_id, b_sum)
        resp_a = client.generate(prompt_a, temperature=0.3, max_tokens=120)
        bump()
        resp_b = client.generate(prompt_b, temperature=0.3, max_tokens=120)
        bump()
        # Judge with robustness
        profile_json = {"user_id": profile.user_id, "OCEAN": {"O": profile.openness, "C": profile.conscientiousness, "E": profile.extraversion, "A": profile.agreeableness, "N": profile.neuroticism}}
        samples_ab: List[Dict[str, Any]] = []
        for _ in range(max(1, n_samples)):
            out = call_judge_samples(client, profile_json, history, scenario_json, card_a_json, card_b_json, n=1, temperature=temperature)
            if out:
                samples_ab.extend(out)
            bump()
        samples_ba: List[Dict[str, Any]] = []
        for _ in range(max(1, n_samples)):
            out = call_judge_samples(client, profile_json, history, scenario_json, card_b_json, card_a_json, n=1, temperature=temperature)
            if out:
                samples_ba.extend(out)
            bump()
        choice, checks, reasons = aggregate_judge_samples(samples_ab, samples_ba)
        chosen_resp = resp_a if choice == "A" else (resp_b if choice == "B" else (resp_a or resp_b))
        likert = scorer.score(chosen_resp)
        bump()  # likert scored
        results.append(
            {
                "user_id": profile.user_id,
                "name": getattr(profile, "name", profile.user_id),
                "action": choice,
                "reasons": reasons,
                "checks": checks,
                "response_A": resp_a,
                "response_B": resp_b,
                "likert": likert,
            }
        )
    return results

