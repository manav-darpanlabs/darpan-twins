import os
from dotenv import load_dotenv, find_dotenv
from typing import Dict, Any, List

from .policy_model import PolicyModel
from .prompts import drivers_to_phrases, build_llm_prompt, fallback_rationale


class LLMClient:
    def __init__(self) -> None:
        # Load .env if present (project root or parent dirs)
        try:
            load_dotenv(find_dotenv(), override=False)
        except Exception:
            pass
        self.provider = os.environ.get("LLM_PROVIDER", "none").lower()
        self.model = os.environ.get("LLM_MODEL", "")
        self.openai_key = os.environ.get("OPENAI_API_KEY")
        self.anthropic_key = os.environ.get("ANTHROPIC_API_KEY")

    def _generate_openai(self, prompt: str, temperature: float = 0.3, max_tokens: int = 256) -> str:
        if not self.openai_key or not self.model:
            return ""
        try:
            try:
                from openai import OpenAI  # type: ignore
                client = OpenAI(api_key=self.openai_key)
                resp = client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return (resp.choices[0].message.content or "").strip()
            except Exception:
                # Fallback for older openai package versions
                import openai  # type: ignore
                openai.api_key = self.openai_key
                resp = openai.ChatCompletion.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return resp["choices"][0]["message"]["content"].strip()
        except Exception:
            return ""

    def _generate_anthropic(self, prompt: str, temperature: float = 0.3, max_tokens: int = 256) -> str:
        if not self.anthropic_key or not self.model:
            return ""
        try:
            import anthropic  # type: ignore
            client = anthropic.Anthropic(api_key=self.anthropic_key)
            msg = client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}],
            )
            try:
                # SDK returns a list of content blocks
                parts = getattr(msg, "content", [])
                texts = []
                for part in parts:
                    text = getattr(part, "text", None)
                    if text:
                        texts.append(text)
                return "\n".join(texts).strip()
            except Exception:
                return ""
        except Exception:
            return ""

    def generate(self, prompt: str, temperature: float = 0.3, max_tokens: int = 256) -> str:
        if self.provider == "openai":
            return self._generate_openai(prompt, temperature=temperature, max_tokens=max_tokens)
        if self.provider in ("anthropic", "claude"):
            return self._generate_anthropic(prompt, temperature=temperature, max_tokens=max_tokens)
        return ""

    # Minimal vision helper (OpenAI only). Accepts base64 image bytes.
    def generate_vision(self, prompt: str, image_b64: str, temperature: float = 0.2, max_tokens: int = 400) -> str:
        if self.provider != "openai" or not self.openai_key or not self.model:
            return ""
        try:
            try:
                from openai import OpenAI  # type: ignore
                client = OpenAI(api_key=self.openai_key)
                messages = [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_b64}",
                                },
                            },
                        ],
                    }
                ]
                resp = client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    response_format={"type": "json_object"},
                )
                return (resp.choices[0].message.content or "").strip()
            except Exception:
                import openai  # type: ignore
                openai.api_key = self.openai_key
                messages = [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_b64}",
                                },
                            },
                        ],
                    }
                ]
                try:
                    resp = openai.ChatCompletion.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    response_format={"type": "json_object"},
                )
                except Exception:
                    resp = openai.ChatCompletion.create(
                        model=self.model,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )
                return resp["choices"][0]["message"]["content"].strip()
        except Exception:
            return ""


class DecisionTool:
    def __init__(self, model_dir: str = "models") -> None:
        self.policy = PolicyModel(model_dir=model_dir)
        self.llm = LLMClient()

    def choose(
        self,
        user_name: str,
        ocean: Dict[str, float],
        context_summary: str,
        context_vec: Dict[str, float],
        card_a: Dict[str, float],
        card_b: Dict[str, float],
    ) -> Dict[str, Any]:
        result = self.policy.predict_action(card_a=card_a, card_b=card_b, context=context_vec)
        action = result.get("action", "A")
        drivers = result.get("drivers", [])
        phrases: List[str] = drivers_to_phrases(drivers)
        # Guardrail: if we somehow only extract personality features (ctx_*), reduce to generic "overall"
        if all(p.startswith("ctx_") or p.startswith("cuisine ") for p in phrases):
            phrases = [p for p in phrases if not p.startswith("ctx_")]
            if not phrases:
                phrases = ["overall value"]

        prompt = build_llm_prompt(
            user_name=user_name,
            ocean=ocean,
            values_top3=phrases[:3],
            context_summary=context_summary,
            action=action,
            drivers=phrases,
        )
        llm_text = self.llm.generate(prompt)
        rationale_source = "llm" if llm_text else "fallback"
        if not llm_text:
            llm_text = fallback_rationale(action, phrases)
        out: Dict[str, Any] = {
            "action": action,
            "rationale": llm_text,
            "prob_A": result.get("prob_A"),
            "score_margin": result.get("score_margin"),
            "drivers": drivers,
            "prompt": prompt,
            "rationale_source": rationale_source,
        }

        return out
