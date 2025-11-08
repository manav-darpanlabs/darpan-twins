import os
import json
from dotenv import load_dotenv, find_dotenv
from typing import Dict, Any, List

from .rag_retriever import RAGRetriever
from .prompts_llm import build_decider_prompt, build_analyst_prompt


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
        """
        Initialize DecisionTool with LLM + RAG architecture.

        Args:
            model_dir: Kept for backward compatibility, but no longer used for ML models
        """
        self.llm = LLMClient()
        self.rag = RAGRetriever(llm_client=self.llm)

    def _call_decider(self, prompt: str) -> str:
        """
        Stage 1: The Decider - Generates natural text decision explanation.

        The Decider makes the restaurant choice and explains reasoning naturally,
        without structured output requirements.

        Args:
            prompt: The comprehensive decision prompt with personality, context, cards

        Returns:
            str: Natural text response (2-3 paragraphs) explaining the decision
        """
        response: str = self.llm.generate(
            prompt,
            temperature=0.3,  # Balanced consistency with natural variation
            max_tokens=500
        )
        return response

    def _call_analyst(self, decider_text: str) -> Dict[str, Any]:
        """
        Stage 2: The Analyst - Extracts structured data from The Decider's text.

        The Analyst parses the natural language response and extracts:
        - choice (A or B)
        - confidence (0.0-1.0)
        - reasoning (summarized)
        - key_factors (list of influencing factors)

        Args:
            decider_text: The Decider's natural text response

        Returns:
            Dict[str, Any]: Extracted structured data with keys:
                - choice (str): "A" or "B"
                - confidence (float): 0.0-1.0
                - reasoning (str): Summarized rationale
                - key_factors (List[str]): Key decision factors
                - extraction_status (str): "success" or error message
        """
        # Build extraction prompt
        analyst_prompt = build_analyst_prompt(decider_text)

        # Call The Analyst with lower temperature (more deterministic)
        analyst_response = self.llm.generate(
            analyst_prompt,
            temperature=0.1,
            max_tokens=300
        )

        # Try to parse JSON response
        try:
            extracted = json.loads(analyst_response)

            # Validate and sanitize extracted data
            choice = str(extracted.get("choice", "A")).upper()
            if choice not in ["A", "B"]:
                choice = "A"

            confidence = float(extracted.get("confidence", 0.5))
            confidence = max(0.0, min(1.0, confidence))  # Clamp to [0, 1]

            reasoning = str(extracted.get("reasoning", ""))[:500]  # Truncate if too long

            key_factors = extracted.get("key_factors", [])
            if not isinstance(key_factors, list):
                key_factors = []

            return {
                "choice": choice,
                "confidence": confidence,
                "reasoning": reasoning,
                "key_factors": key_factors,
                "extraction_status": "success"
            }

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            # Fallback: Use defaults
            return {
                "choice": "A",
                "confidence": 0.5,
                "reasoning": decider_text[:200] if decider_text else "Unable to extract reasoning.",
                "key_factors": [],
                "extraction_status": f"failed: {str(e)}"
            }

    def choose(
        self,
        user_name: str,
        ocean: Dict[str, float],
        context_summary: str,
        context_vec: Dict[str, float],
        card_a: Dict[str, float],
        card_b: Dict[str, float],
    ) -> Dict[str, Any]:
        """
        Make a decision between two restaurant cards using multi-stage LLM pipeline with RAG.

        Pipeline:
            1. RAG Retrieval: Find 10 similar past decisions based on personality/context
            2. Stage 1 (The Decider): Generate natural text explanation of choice
            3. Stage 2 (The Analyst): Extract structured data from natural text
            4. Return combined results with full pipeline metadata

        Args:
            user_name: User identifier or name
            ocean: OCEAN personality traits (openness, conscientiousness, etc.)
            context_summary: Human-readable context (e.g., "19:00, weekday, 28°C")
            context_vec: Full context features including demographics
            card_a: Restaurant A attributes (rating, price, distance, etc.)
            card_b: Restaurant B attributes (rating, price, distance, etc.)

        Returns:
            Dict[str, Any] with keys:
                - action (str): "A" or "B" - the chosen card
                - rationale (str): Natural language explanation
                - confidence (float): 0.0-1.0 confidence score
                - key_factors (List[str]): Main decision factors
                - prompt (str): Full prompt sent to Decider (for debugging)
                - decider_response (str): Raw Decider output
                - analyst_extraction (Dict): Raw Analyst output
                - agent_pipeline (Dict): Pipeline status metadata
                - Legacy fields set to None: prob_A, score_margin, drivers
        """
        # 1. Retrieve similar past decisions from RAG
        similar_decisions = self.rag.get_similar(
            user_profile=ocean,
            context=context_vec,
            k=10
        )

        # 2. Build comprehensive decision prompt for The Decider
        decider_prompt = build_decider_prompt(
            user_name=user_name,
            ocean=ocean,
            demographics=context_vec,
            context_summary=context_summary,
            card_a=card_a,
            card_b=card_b,
            past_decisions=similar_decisions
        )

        # 3. Stage 1: The Decider generates natural text response
        decider_response = self._call_decider(decider_prompt)

        # 4. Stage 2: The Analyst extracts structured data
        analyst_extraction = self._call_analyst(decider_response)

        # 5. Build output (maintaining backward-compatible interface)
        out: Dict[str, Any] = {
            # Primary outputs (from The Analyst)
            "action": analyst_extraction["choice"],
            "rationale": analyst_extraction["reasoning"],
            "confidence": analyst_extraction["confidence"],
            "key_factors": analyst_extraction["key_factors"],

            # Pipeline metadata
            "prompt": decider_prompt,
            "decider_response": decider_response,
            "analyst_extraction": analyst_extraction,
            "agent_pipeline": {
                "stage_1": "The Decider",
                "stage_2": "The Analyst",
                "extraction_status": analyst_extraction.get("extraction_status", "unknown")
            },

            # Legacy fields for backward compatibility (set to None)
            "prob_A": None,
            "score_margin": None,
            "drivers": [],
            "rationale_source": "multi_stage_llm"
        }

        return out
