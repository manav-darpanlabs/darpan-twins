from dataclasses import dataclass
from typing import Dict, Any
import json


def _clip01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


@dataclass
class TwinProfile:
    user_id: str
    openness: float
    conscientiousness: float
    extraversion: float
    agreeableness: float
    neuroticism: float
    name: str = "Customer"

    @staticmethod
    def from_json(path: str) -> "TwinProfile":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        traits = data.get("OCEAN", {})
        return TwinProfile(
            user_id=data.get("user_id") or data.get("id") or "USER",
            openness=_clip01(traits.get("openness", 0.5)),
            conscientiousness=_clip01(traits.get("conscientiousness", 0.5)),
            extraversion=_clip01(traits.get("extraversion", 0.5)),
            agreeableness=_clip01(traits.get("agreeableness", 0.5)),
            neuroticism=_clip01(traits.get("neuroticism", 0.5)),
            name=data.get("name", "Customer"),
        )

    def to_context(self) -> Dict[str, float]:
        # Derived knobs aligned with the synthetic generator
        novelty_seeking = _clip01((self.openness * 0.7) + (1 - self.conscientiousness) * 0.3)
        budget_sensitivity = _clip01((1 - self.conscientiousness) * 0.5 + self.neuroticism * 0.5)
        distance_tolerance = _clip01((self.extraversion * 0.6) + self.openness * 0.2 - self.neuroticism * 0.3)
        rating_focus = _clip01((self.agreeableness * 0.4) + self.conscientiousness * 0.6)
        return {
            "openness": self.openness,
            "conscientiousness": self.conscientiousness,
            "extraversion": self.extraversion,
            "agreeableness": self.agreeableness,
            "neuroticism": self.neuroticism,
            "novelty_seeking": novelty_seeking,
            "budget_sensitivity": budget_sensitivity,
            "distance_tolerance": distance_tolerance,
            "rating_focus": rating_focus,
        }

    def style_tokens(self) -> Dict[str, Any]:
        # Simple tone knobs to flavor chat text
        enthusiasm = 0.3 + 0.7 * self.extraversion
        politeness = 0.4 + 0.6 * self.agreeableness
        brevity = 0.6 + 0.4 * self.conscientiousness
        return {
            "enthusiasm": round(enthusiasm, 2),
            "politeness": round(politeness, 2),
            "brevity": round(brevity, 2),
        }

    def greeting(self) -> str:
        if self.extraversion > 0.6:
            return f"Hey there! I'm {self.name}'s twin."
        if self.agreeableness > 0.6:
            return f"Hi! I'm {self.name}'s twin—happy to help."
        return f"Hello. I'm {self.name}'s twin."

