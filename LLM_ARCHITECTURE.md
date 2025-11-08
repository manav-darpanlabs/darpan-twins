# LLM-Only Architecture for Digital Twins

## Overview

This document describes the **pure LLM-based architecture** for digital twin decision-making, replacing the previous hybrid ML+LLM approach with a RAG (Retrieval-Augmented Generation) system.

### Key Principles

1. **No ML Models**: LLMs make all decisions via prompt engineering and RAG context
2. **No Training Required**: System works with pre-trained LLMs (GPT-4, Claude, etc.)
3. **Personality-Driven**: Decisions reflect OCEAN personality traits through comprehensive prompts
4. **RAG as "Soft Training"**: Past decisions provide context without gradient updates
5. **Structured Output**: JSON responses enable programmatic decision handling

---

## Architecture Components

### 1. RAG Example Database

**Purpose**: Provides contextual examples of past decisions for LLM prompts

**File**: [data/rag_examples.json](data/rag_examples.json)
- **Size**: 13 MB
- **Examples**: 10,000 diverse past decisions
- **Source**: Sampled from 300K training interactions

**Example Structure**:
```json
{
  "user_id": "USER_042",
  "ocean": {
    "openness": 0.73,
    "conscientiousness": 0.52,
    "extraversion": 0.61,
    "agreeableness": 0.48,
    "neuroticism": 0.35
  },
  "demographics": {
    "age": 28,
    "income": 750000,
    "gender": "female"
  },
  "context_summary": "19:00 (evening), weekday, 28°C",
  "decision": {
    "action": "A",
    "rationale_category": "rating"
  },
  "reasoning": "Chose A: significantly better rating (4.7⭐ vs 4.3⭐), matches adventurous personality"
}
```

**Generation**: [scripts/build_rag_examples.py](scripts/build_rag_examples.py)

---

### 2. RAG Retriever

**Purpose**: Retrieves k similar past decisions based on user personality and context

**File**: [twins/rag_retriever.py](twins/rag_retriever.py:14)

**Key Features**:
- **Embedding-based similarity**: Uses OpenAI `text-embedding-3-small` for semantic search
- **Cosine similarity**: Finds k=10 most similar past decisions
- **Fallback**: Simple feature matching if embeddings unavailable
- **Caching**: Stores embeddings to disk for performance

**Query Format**:
```
User Profile:
- Personality: O=0.73, C=0.52, E=0.61, A=0.48, N=0.35
- Age: 28, Income: ₹750,000

Context: 19:00, weekday, 28°C
```

**Retrieval Process**:
1. Convert query to embedding (1536 dimensions)
2. Compute cosine similarity with all examples
3. Return top-k matches
4. Format for prompt inclusion

---

### 3. Decision Prompt Builder

**Purpose**: Creates comprehensive prompts that guide LLM decision-making

**File**: [twins/prompts_llm.py](twins/prompts_llm.py:11)

**Prompt Structure**:

#### A. User Profile Section
- **OCEAN Traits** with interpretations (0-1 scale)
- **Demographics** (age, gender, income)
- **Derived Preferences** (novelty seeking, budget sensitivity, etc.)

#### B. Past Behavior Section
- Retrieved RAG examples (5 most similar)
- Formatted with personality traits, context, choice, reasoning

#### C. Current Decision Section
- **Card A** details (name, cuisine, rating, price, time, distance, coupons)
- **Card B** details (same attributes)
- **Context** (time, weather, day type)

#### D. Personality-Driven Guidelines
Dynamic guidance based on trait levels:
- **High Openness** (>0.7): "Novel cuisines strongly appeal to you"
- **High Conscientiousness** (>0.7): "Ratings and reviews matter a lot"
- **High Neuroticism** (>0.7): "High ratings reduce anxiety"
- **High Budget Sensitivity** (>0.7): "Price is a major factor"

#### E. Task Instructions
- Output format: JSON with `{choice, confidence, reasoning, key_factors}`
- Consistency requirements
- Personality alignment requirements

**Example Prompt** (abbreviated):
```
[SYSTEM] You are simulating Alice, a food delivery customer...

## USER PROFILE
**Personality (OCEAN Traits)**:
  • Openness: 0.73 (adventurous/creative)
  • Conscientiousness: 0.52 (balanced)
  ...

## YOUR PAST BEHAVIOR
1. User (O=0.71, C=0.54) → Chose A: Novel sushi over familiar pizza
2. User (O=0.75, C=0.48) → Chose B: Better rating despite longer delivery
...

## TODAY'S DECISION
**Card A: Sushi Express**
  • Cuisine: sushi (novel)
  • Rating: 4.7⭐ (2,350 reviews)
  • Price: ₹450 | Time: 35 min | Distance: 4.2 km

**Card B: Pizza Palace**
  • Cuisine: pizza (familiar)
  • Rating: 4.3⭐ (1,840 reviews)
  • Price: ₹280 | Time: 25 min | Distance: 2.1 km | Coupon: FLAT20

## PERSONALITY-DRIVEN DECISION GUIDELINES
High Openness (0.73):
  • Novel cuisines (sushi, Thai) strongly appeal to you
  • Willing to try less-reviewed places for unique experiences

## TASK
Output ONLY valid JSON:
{"choice": "A" or "B", "confidence": 0.0-1.0, "reasoning": "...", "key_factors": [...]}
```

---

### 4. DecisionTool (LLM+RAG)

**Purpose**: Core decision-making component using LLM with RAG context

**File**: [twins/tools.py](twins/tools.py:150)

**Flow**:
```python
class DecisionTool:
    def __init__(self):
        self.llm = LLMClient()
        self.rag = RAGRetriever(llm_client=self.llm)

    def choose(self, user_name, ocean, context_vec, card_a, card_b):
        # 1. Retrieve similar past decisions
        similar_decisions = self.rag.get_similar(
            user_profile=ocean,
            context=context_vec,
            k=10
        )

        # 2. Build comprehensive prompt
        prompt = build_decision_prompt(
            user_name, ocean, context_vec,
            card_a, card_b, similar_decisions
        )

        # 3. LLM makes decision
        llm_response = self.llm.generate(
            prompt,
            temperature=0.3,
            max_tokens=500
        )

        # 4. Parse JSON response
        decision = json.loads(llm_response)

        return {
            "action": decision["choice"],
            "rationale": decision["reasoning"],
            "confidence": decision["confidence"],
            "key_factors": decision["key_factors"]
        }
```

**Changes from Previous Architecture**:
- ❌ **Removed**: `PolicyModel` (XGBoost classifier)
- ❌ **Removed**: `predict_action()` (ML prediction)
- ❌ **Removed**: `drivers_to_phrases()` (feature importance)
- ✅ **Added**: `RAGRetriever` (similarity search)
- ✅ **Added**: `build_decision_prompt()` (comprehensive prompts)
- ✅ **Added**: JSON parsing with fallback

---

### 5. TwinRuntime (Interface Layer)

**Purpose**: High-level API for twin interactions

**File**: [twins/twin_runtime.py](twins/twin_runtime.py:28)

**Interface** (unchanged):
```python
class TwinRuntime:
    def __init__(self, profile: TwinProfile):
        self.profile = profile
        self.tool = DecisionTool()
        self.memory = MemoryStore()

    def choose_between_cards(self, card_a, card_b, context):
        # Merges profile traits with runtime context
        # Calls DecisionTool.choose()
        # Saves to memory
        # Returns result with metadata
```

**Output Format**:
```python
{
    "user_id": "USER_042",
    "action": "A",
    "rationale": "Chose A: better rating and novel cuisine matches my adventurous personality",
    "chat": "...",  # Same as rationale
    "meta": {
        "confidence": 0.82,
        "key_factors": ["rating", "novelty", "personality_fit"],
        "prompt": "...",  # Full prompt for debugging
        "memories": [...]  # Past decisions
    }
}
```

---

## Decision Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. User Input                                               │
│    - User Profile (OCEAN traits, demographics)             │
│    - Card A & B (restaurant attributes)                    │
│    - Context (time, weather, etc.)                         │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. RAG Retrieval                                            │
│    - Convert user profile + context to embedding           │
│    - Search rag_examples.json for k=10 similar cases       │
│    - Retrieve: personalities, contexts, choices, reasons   │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Prompt Construction                                      │
│    - Build comprehensive prompt with:                       │
│      • User personality interpretation                      │
│      • Past behavior examples (from RAG)                    │
│      • Current card details                                 │
│      • Personality-driven guidelines                        │
│      • Structured JSON output schema                        │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. LLM Decision-Making                                      │
│    - Send prompt to LLM (GPT-4/Claude)                      │
│    - Temperature: 0.3 (balanced consistency/creativity)     │
│    - Max tokens: 500                                        │
│    - Response format: JSON                                  │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Response Parsing                                         │
│    - Parse JSON: {choice, confidence, reasoning, factors}   │
│    - Fallback if invalid JSON                               │
│    - Save to memory store                                   │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. Output                                                   │
│    - Action: "A" or "B"                                     │
│    - Rationale: Natural language explanation               │
│    - Metadata: Confidence, factors, prompt                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Testing & Validation

### 1. Consistency Test

**Script**: [scripts/test_llm_consistency.py](scripts/test_llm_consistency.py)

**Purpose**: Verify LLM makes consistent decisions when given same input

**Method**:
- Present same choice to twin 10 times
- Count how many times it chooses same card
- Target: >80% consistency (8/10)

**Usage**:
```bash
python scripts/test_llm_consistency.py --user_id USER_042 --runs 10
```

**Expected Output**:
```
Consistency: 90% (9/10 chose 'A')
Avg Confidence: 0.78
Status: ✓ PASS
```

### 2. Personality Alignment Test

**Script**: [scripts/test_personality_alignment.py](scripts/test_personality_alignment.py)

**Purpose**: Verify personality traits influence decisions as expected

**Method**:
- Test high-openness users (O > 0.7) vs low-openness (O < 0.3)
- Present novel (sushi) vs familiar (pizza) with equal attributes
- Measure: High-O should choose novel more often

**Usage**:
```bash
python scripts/test_personality_alignment.py --users 20 --verbose
```

**Expected Output**:
```
High-Openness Novel Rate: 75%
Low-Openness Novel Rate: 30%
Status: ✓ PASS - Personality alignment confirmed!
```

---

## Setup Instructions

### 1. Environment Setup

Create [.env](.env.example) file:
```bash
cp .env.example .env
```

Edit `.env`:
```bash
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini  # Recommended for cost
OPENAI_API_KEY=sk-...

RAG_EXAMPLES_PATH=data/rag_examples.json
RAG_EMBEDDING_CACHE=data/rag_embeddings.npy
RAG_K_NEIGHBORS=10
```

### 2. Generate RAG Database

```bash
python scripts/build_rag_examples.py \
  --input data/train_expanded.csv \
  --output data/rag_examples.json \
  --max_examples 10000 \
  --seed 42
```

**Output**:
- `data/rag_examples.json` (13 MB)
- 10,000 diverse decision examples

### 3. Run Tests

**Consistency Test**:
```bash
python scripts/test_llm_consistency.py --user_id USER_001 --runs 10
```

**Personality Alignment Test**:
```bash
python scripts/test_personality_alignment.py --users 20
```

### 4. Run Streamlit App

```bash
streamlit run app_streamlit.py
```

**Features**:
- Live twin interactions
- View prompts, RAG examples, confidence
- Test different users and scenarios

---

## Performance Considerations

### Latency
- **Target**: <3 seconds per decision
- **Breakdown**:
  - RAG retrieval: ~0.1s (with cached embeddings)
  - LLM inference: ~1-2s (GPT-4o-mini)
  - Parsing: <0.1s

**Optimization**:
- Use cached embeddings (avoid regenerating)
- Use faster models (GPT-4o-mini vs GPT-4)
- Batch requests if handling multiple decisions

### Cost
- **Target**: <$0.01 per decision
- **Breakdown**:
  - Embeddings: $0.00002 per query (text-embedding-3-small)
  - LLM inference: $0.0015-$0.003 per decision (GPT-4o-mini)

**Cost Optimization**:
- Use GPT-4o-mini instead of GPT-4 (10x cheaper)
- Cache embeddings (avoid regeneration)
- Use temperature=0.3 (fewer retries needed)

### Quality Metrics

**Success Criteria**:
- ✅ Consistency: >80% (8/10 runs same choice)
- ✅ Personality alignment: High-O → novel > Low-O → novel
- ✅ Confidence calibration: High confidence → correct more often
- ✅ Latency: <3 seconds per decision
- ✅ Cost: <$0.01 per decision

---

## Comparison: Hybrid ML vs Pure LLM

| Aspect | Hybrid ML+LLM (OLD) | Pure LLM+RAG (NEW) |
|--------|---------------------|-------------------|
| **Decision Making** | XGBoost classifier | LLM with RAG context |
| **Rationale Generation** | LLM only | LLM (integrated) |
| **Training Required** | Yes (XGBoost on 300K rows) | No (pre-trained LLM) |
| **Personality Influence** | Feature engineering | Prompt engineering |
| **Context Memory** | None | RAG retrieval (10 examples) |
| **Consistency** | 100% (deterministic) | 80-90% (temperature=0.3) |
| **Latency** | ~0.5s (ML) + ~1.5s (LLM) | ~2-3s (LLM only) |
| **Cost per Decision** | Near zero (local inference) | ~$0.002 (API calls) |
| **Interpretability** | SHAP values + rationale | Reasoning + key factors |
| **Maintenance** | Model retraining required | Prompt updates only |
| **Scalability** | Batch training bottleneck | Instant deployment |

**Key Advantages of LLM-Only**:
- ✅ No training pipeline needed
- ✅ Instant updates via prompt engineering
- ✅ Better natural language understanding
- ✅ More nuanced personality handling
- ✅ Easier to debug (read prompts)

**Trade-offs**:
- ⚠️ API costs (~$0.002 per decision)
- ⚠️ Slightly lower consistency (80-90% vs 100%)
- ⚠️ Requires internet connection
- ⚠️ Dependent on LLM provider availability

---

## Future Enhancements

### 1. Multi-Sample Voting
- Run LLM 3x with low temperature
- Take majority vote for final decision
- Improves consistency to 95%+
- Trade-off: 3x cost, 3x latency

### 2. Confidence Calibration
- Track: confidence vs actual correctness
- Adjust confidence scores based on historical performance
- Warn user if low-confidence decision

### 3. Memory Integration
- Use [twins/memory_store.py](twins/memory_store.py) for user-specific memory
- Include past N decisions in prompt (not just similar ones)
- Track preference drift over time

### 4. Dynamic RAG Updates
- Add new decisions to RAG database in real-time
- Incremental embedding updates
- Maintain recency bias

### 5. Multi-LLM Ensemble
- Run same prompt on GPT-4 and Claude simultaneously
- Compare responses for consistency
- Use for high-stakes decisions

---

## Troubleshooting

### Issue: Low Consistency (<80%)

**Possible Causes**:
- Temperature too high
- Ambiguous card differences
- Conflicting personality traits

**Solutions**:
- Lower temperature (try 0.2 or 0.1)
- Review prompt guidelines for clarity
- Test with users with clear trait extremes

### Issue: No RAG Examples Loaded

**Error**: `⚠️ RAG examples not found at data/rag_examples.json`

**Solution**:
```bash
python scripts/build_rag_examples.py --input data/train_expanded.csv
```

### Issue: Embeddings Regenerating Every Time

**Cause**: Embedding cache not found or corrupted

**Solution**:
- Check `data/rag_embeddings.npy` exists
- If corrupted, delete and regenerate:
```bash
rm data/rag_embeddings.npy
python scripts/test_llm_consistency.py  # Will regenerate
```

### Issue: API Key Errors

**Error**: `openai.error.AuthenticationError`

**Solution**:
- Verify `.env` file exists
- Check `OPENAI_API_KEY` is set correctly
- Test: `echo $OPENAI_API_KEY` (should show key)

---

## File Reference

### Core Components
- [twins/tools.py](twins/tools.py:150) - DecisionTool (LLM+RAG integration)
- [twins/rag_retriever.py](twins/rag_retriever.py:14) - RAG similarity search
- [twins/prompts_llm.py](twins/prompts_llm.py:11) - Comprehensive prompt builder
- [twins/twin_runtime.py](twins/twin_runtime.py:28) - High-level API

### Data & Scripts
- [data/rag_examples.json](data/rag_examples.json) - RAG database (10K examples)
- [scripts/build_rag_examples.py](scripts/build_rag_examples.py) - RAG database builder
- [scripts/test_llm_consistency.py](scripts/test_llm_consistency.py) - Consistency test
- [scripts/test_personality_alignment.py](scripts/test_personality_alignment.py) - Personality test

### Configuration
- [.env.example](.env.example) - Environment template
- [LLM_MIGRATION_STATUS.md](LLM_MIGRATION_STATUS.md) - Migration tracking

### Backup (Removed ML Files)
- `models_backup/` - Archived ML models and training scripts
  - `policy_model.py` - XGBoost-based policy
  - `train_policy.py` - Training script
  - `*.pkl` - Trained model files

---

## Contact & Support

For questions about the LLM-only architecture:
1. Review this document for architecture details
2. Check [LLM_MIGRATION_STATUS.md](LLM_MIGRATION_STATUS.md) for migration status
3. Run test scripts to verify setup
4. Check `.env` configuration

**Architecture Version**: v3.0 (LLM-only with RAG)
**Last Updated**: November 2025
**Status**: ✅ Production-ready
