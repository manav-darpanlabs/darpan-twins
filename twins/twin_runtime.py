from typing import Dict, Any, List

from .twin_profile import TwinProfile
from .tools import DecisionTool
from .memory_store import MemoryStore


def summarize_context(context: Dict[str, Any]) -> str:
    parts: List[str] = []
    hour = context.get("hour_of_day")
    if hour is not None:
        parts.append(f"at {int(hour)}:00")
    if context.get("is_weekend"):
        parts.append("on the weekend")
    temp = context.get("temperature_c")
    if temp is not None:
        parts.append(f"~{float(temp):.0f}°C")
    precip = context.get("precip_mm")
    if precip is not None and float(precip) > 0:
        parts.append(f"rain {float(precip):.1f}mm")
    # demographics brief
    income = context.get("dem_income")
    if income is not None:
        parts.append(f"annual income ₹{float(income):.0f}")
    return ", ".join(parts) if parts else "current conditions"


class TwinRuntime:
    def __init__(self, profile: TwinProfile, model_dir: str = "models", memory_path: str = "data/memory_store.json") -> None:
        self.profile = profile
        self.tool = DecisionTool(model_dir=model_dir)
        self.memory = MemoryStore(memory_path)

    @classmethod
    def from_profile_path(cls, path: str, model_dir: str = "models", memory_path: str = "data/memory_store.json") -> "TwinRuntime":
        profile = TwinProfile.from_json(path)
        return cls(profile=profile, model_dir=model_dir, memory_path=memory_path)

    def choose_between_cards(self, card_a: Dict[str, float], card_b: Dict[str, float], runtime_context: Dict[str, float]) -> Dict[str, Any]:
        profile_ctx = self.profile.to_context()
        context_vec = {**runtime_context, **profile_ctx}
        context_summary = summarize_context(runtime_context)

        # retrieve memories (optional use in future prompts)
        memories = self.memory.retrieve(self.profile.user_id, context_summary, k=3)

        result = self.tool.choose(
            user_name=getattr(self.profile, "name", self.profile.user_id),
            ocean={
                "openness": self.profile.openness,
                "conscientiousness": self.profile.conscientiousness,
                "extraversion": self.profile.extraversion,
                "agreeableness": self.profile.agreeableness,
                "neuroticism": self.profile.neuroticism,
            },
            context_summary=context_summary,
            context_vec=context_vec,
            card_a=card_a,
            card_b=card_b,
        )

        # Save a memory
        self.memory.append(
            user_id=self.profile.user_id,
            context_summary=context_summary,
            action=result["action"],
            rationale=result["rationale"],
        )

        return {
            "user_id": self.profile.user_id,
            "action": result["action"],
            "rationale": result["rationale"],
            "chat": result["rationale"],
            "meta": {
                "confidence": result.get("confidence"),
                "key_factors": result.get("key_factors", []),
                "prompt": result.get("prompt"),
                "memories": memories,

                # Multi-stage LLM pipeline metadata
                "decider_response": result.get("decider_response"),
                "analyst_extraction": result.get("analyst_extraction"),
                "agent_pipeline": result.get("agent_pipeline"),

                # Legacy fields (now None for LLM-only architecture)
                "prob_A": result.get("prob_A"),
                "score_margin": result.get("score_margin"),
                "drivers": result.get("drivers"),
            },
        }
