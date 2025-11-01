import json
import os
from typing import Any, Dict, List, Optional, Tuple


class MemoryStore:
    def __init__(self, path: str = "data/memory_store.json") -> None:
        self.path = path
        self._mem: List[Dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    self._mem = json.load(f)
            except Exception:
                self._mem = []

    def _save(self) -> None:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self._mem, f, ensure_ascii=False, indent=2)

    def append(self, user_id: str, context_summary: str, action: str, rationale: str) -> None:
        self._mem.append(
            {
                "user_id": user_id,
                "context_summary": context_summary,
                "action": action,
                "rationale": rationale,
            }
        )
        self._save()

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        return [t.lower() for t in text.split() if t.isascii()]

    @staticmethod
    def _jaccard(a: List[str], b: List[str]) -> float:
        sa, sb = set(a), set(b)
        if not sa or not sb:
            return 0.0
        return len(sa & sb) / float(len(sa | sb))

    def retrieve(self, user_id: str, query: str, k: int = 3) -> List[Dict[str, Any]]:
        q_tokens = self._tokenize(query)
        candidates = [m for m in self._mem if m.get("user_id") == user_id]
        scored: List[Tuple[float, Dict[str, Any]]] = []
        for m in candidates:
            score = self._jaccard(q_tokens, self._tokenize(m.get("context_summary", "")))
            scored.append((score, m))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [m for s, m in scored[:k] if s > 0.0]

