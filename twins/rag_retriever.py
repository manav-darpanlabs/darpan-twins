"""
RAG (Retrieval-Augmented Generation) retriever for past decision examples.

Uses embeddings to find similar contexts and personalities, providing
relevant examples for LLM prompts to ensure consistent decision-making.
"""

import json
import numpy as np
from typing import List, Dict, Any, Optional
from pathlib import Path


class RAGRetriever:
    """
    Retrieves similar past decisions for prompt context.

    Uses OpenAI embeddings API for semantic similarity search.
    Falls back to simple feature matching if embeddings unavailable.
    """

    def __init__(self,
                 examples_path: str = "data/rag_examples.json",
                 embedding_cache_path: str = "data/rag_embeddings.npy",
                 llm_client=None):
        """
        Initialize RAG retriever.

        Args:
            examples_path: Path to JSON file with past decisions
            embedding_cache_path: Path to cached embeddings
            llm_client: LLMClient instance for generating embeddings
        """
        self.examples_path = Path(examples_path)
        self.embedding_cache_path = Path(embedding_cache_path)
        self.llm_client = llm_client

        # Load examples
        self.examples = self._load_examples()

        # Load or generate embeddings
        self.embeddings = self._load_or_generate_embeddings()

    def _load_examples(self) -> List[Dict]:
        """Load past decision examples from JSON."""
        if not self.examples_path.exists():
            print(f"⚠️  RAG examples not found at {self.examples_path}")
            print(f"    Run: python scripts/build_rag_examples.py")
            return []

        try:
            with open(self.examples_path) as f:
                examples = json.load(f)
            print(f"✓ Loaded {len(examples):,} RAG examples from {self.examples_path}")
            return examples
        except Exception as e:
            print(f"✗ Error loading RAG examples: {e}")
            return []

    def _load_or_generate_embeddings(self) -> np.ndarray:
        """Load cached embeddings or generate new ones."""
        # Try to load cache
        if self.embedding_cache_path.exists():
            try:
                embeddings = np.load(self.embedding_cache_path)
                print(f"✓ Loaded {len(embeddings):,} cached embeddings")
                return embeddings
            except Exception as e:
                print(f"⚠️  Error loading embedding cache: {e}")

        # Generate new embeddings
        if not self.examples or not self.llm_client:
            print(f"⚠️  Cannot generate embeddings (no examples or LLM client)")
            return np.array([])

        print(f"Generating embeddings for {len(self.examples):,} examples...")
        print(f"  This may take a few minutes...")

        embeddings = []
        batch_size = 100

        for i in range(0, len(self.examples), batch_size):
            batch = self.examples[i:i+batch_size]
            batch_embeddings = []

            for ex in batch:
                text = self._format_example_for_embedding(ex)
                emb = self._get_embedding(text)
                batch_embeddings.append(emb)

            embeddings.extend(batch_embeddings)

            # Progress
            if (i + batch_size) % 1000 == 0 or i + batch_size >= len(self.examples):
                print(f"  Generated {min(i + batch_size, len(self.examples)):,}/{len(self.examples):,}")

        embeddings = np.array(embeddings)

        # Cache for future use
        try:
            self.embedding_cache_path.parent.mkdir(parents=True, exist_ok=True)
            np.save(self.embedding_cache_path, embeddings)
            print(f"✓ Cached embeddings to {self.embedding_cache_path}")
        except Exception as e:
            print(f"⚠️  Could not cache embeddings: {e}")

        return embeddings

    def _format_example_for_embedding(self, example: Dict) -> str:
        """Format example as text for embedding."""
        ocean = example['ocean']
        demo = example['demographics']
        ctx = example['context']
        dec = example['decision']

        return f"""User Profile:
- Personality: Openness={ocean['openness']:.2f}, Conscientiousness={ocean['conscientiousness']:.2f}, Extraversion={ocean['extraversion']:.2f}, Agreeableness={ocean['agreeableness']:.2f}, Neuroticism={ocean['neuroticism']:.2f}
- Age: {demo['age']}, Gender: {demo['gender']}, Income: ₹{demo['income']:,.0f}

Context: {example['context_summary']}

Decision: {dec['action']}
Reasoning: {example['reasoning']}"""

    def _get_embedding(self, text: str) -> np.ndarray:
        """Get embedding for text using LLM provider."""
        if not self.llm_client:
            return self._simple_feature_vector(text)

        try:
            if self.llm_client.provider == "openai":
                import openai
                client = openai.OpenAI(api_key=self.llm_client.openai_key)
                response = client.embeddings.create(
                    model="text-embedding-3-small",
                    input=text
                )
                return np.array(response.data[0].embedding)

            elif self.llm_client.provider in ("anthropic", "claude"):
                # Anthropic doesn't have embeddings API
                # Fall back to simple feature matching
                return self._simple_feature_vector(text)

        except Exception as e:
            print(f"⚠️  Embedding error: {e}")
            return self._simple_feature_vector(text)

        return np.zeros(1536)  # Default embedding size

    def _simple_feature_vector(self, text: str) -> np.ndarray:
        """
        Fallback: simple feature extraction without embeddings API.

        Creates a feature vector from text characteristics.
        Not as good as semantic embeddings but works without API.
        """
        # Extract simple features
        features = []

        # Length features
        features.append(len(text) / 1000)  # Normalized length
        features.append(text.count('\n') / 10)  # Line count

        # Keyword presence (simple bag of words)
        keywords = [
            'rating', 'price', 'delivery', 'distance', 'coupon', 'discount',
            'rain', 'hot', 'cold', 'evening', 'morning', 'weekend',
            'openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism'
        ]
        for kw in keywords:
            features.append(1.0 if kw.lower() in text.lower() else 0.0)

        # Pad to 1536 dimensions (OpenAI embedding size)
        while len(features) < 1536:
            features.append(0.0)

        return np.array(features[:1536])

    def get_similar(self,
                    user_profile: Dict[str, float],
                    context: Dict[str, float],
                    k: int = 10) -> List[Dict]:
        """
        Retrieve k most similar past decisions.

        Args:
            user_profile: OCEAN traits dict
            context: Current context (weather, time, demographics, etc.)
            k: Number of examples to retrieve

        Returns:
            List of similar past decisions
        """
        if len(self.examples) == 0:
            print("⚠️  No RAG examples available")
            return []

        # Create query text
        query_text = self._format_query(user_profile, context)

        # Get query embedding
        query_emb = self._get_embedding(query_text)

        # Compute cosine similarity
        if self.embeddings.size > 0 and len(self.embeddings) == len(self.examples):
            similarities = self._cosine_similarity(query_emb, self.embeddings)
            top_k_idx = np.argsort(similarities)[-k:][::-1]
            return [self.examples[i] for i in top_k_idx]

        # Fallback: return random diverse examples
        print("⚠️  Using fallback retrieval (random sampling)")
        import random
        return random.sample(self.examples, min(k, len(self.examples)))

    def _format_query(self, user_profile: Dict, context: Dict) -> str:
        """Format current context as query text."""
        # Extract values
        age = context.get('dem_age', 30)
        income = context.get('dem_income', 600000)
        hour = context.get('hour_of_day', 12)
        is_weekend = context.get('is_weekend', 0)
        temp = context.get('temperature_c', 24)
        precip = context.get('precip_mm', 0)

        # Format
        return f"""User Profile:
- Personality: Openness={user_profile.get('openness', 0.5):.2f}, Conscientiousness={user_profile.get('conscientiousness', 0.5):.2f}, Extraversion={user_profile.get('extraversion', 0.5):.2f}, Agreeableness={user_profile.get('agreeableness', 0.5):.2f}, Neuroticism={user_profile.get('neuroticism', 0.5):.2f}
- Age: {age}, Income: ₹{income:,.0f}

Context: {hour}:00, {'weekend' if is_weekend else 'weekday'}, {temp:.0f}°C{', rain' if precip > 0 else ''}"""

    def _cosine_similarity(self, query: np.ndarray, embeddings: np.ndarray) -> np.ndarray:
        """Compute cosine similarity between query and all embeddings."""
        # Normalize
        query_norm = query / (np.linalg.norm(query) + 1e-8)
        embeddings_norm = embeddings / (np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-8)

        # Dot product
        similarities = np.dot(embeddings_norm, query_norm)
        return similarities

    def format_for_prompt(self, examples: List[Dict], max_length: int = 5) -> str:
        """
        Format retrieved examples for inclusion in LLM prompt.

        Args:
            examples: List of retrieved examples
            max_length: Maximum number of examples to include

        Returns:
            Formatted string for prompt
        """
        if not examples:
            return "No similar past decisions available."

        lines = []
        for i, ex in enumerate(examples[:max_length]):
            ocean = ex['ocean']
            demo = ex['demographics']
            lines.append(f"""
{i+1}. **Similar User** (O={ocean['openness']:.2f}, C={ocean['conscientiousness']:.2f}, E={ocean['extraversion']:.2f}, A={ocean['agreeableness']:.2f}, N={ocean['neuroticism']:.2f})
   - Age: {demo['age']}, Income: ₹{demo['income']:,.0f}
   - Context: {ex['context_summary']}
   - Choice: {ex['decision']['action']}
   - Reasoning: {ex['reasoning']}""")

        return "\n".join(lines)
