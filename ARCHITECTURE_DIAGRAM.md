# DARPAN TWINS LAB - ARCHITECTURE DIAGRAMS

## 1. System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                      DARPAN TWINS LAB                               │
│                    (LLM-based Digital Twin)                         │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────────┐
│   User Interface     │
│  (Streamlit App)     │
│ - Location Select    │
│ - Card Upload        │
│ - Results Dashboard  │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐    ┌─────────────────────┐
│  Data Processing     │    │  Weather API        │
│  - Image Parsing     │──▶ │  (Open-Meteo)       │
│  - Card Validation   │    │  - Temperature      │
│                      │    │  - Precipitation    │
└──────────┬───────────┘    └─────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────┐
│           Twin Decision Engine                       │
│  ┌──────────────────────────────────────────────┐   │
│  │        Multi-Stage LLM Pipeline              │   │
│  │                                              │   │
│  │  1. RAG Retrieval                            │   │
│  │     └─▶ Find 10 similar past decisions       │   │
│  │                                              │   │
│  │  2. The Decider (Stage 1)                    │   │
│  │     └─▶ Generate natural text explanation    │   │
│  │        (temperature: 0.3)                    │   │
│  │                                              │   │
│  │  3. The Analyst (Stage 2)                    │   │
│  │     └─▶ Extract structured JSON             │   │
│  │        (temperature: 0.1)                    │   │
│  └──────────────────────────────────────────────┘   │
└────────────────┬─────────────────────────────────────┘
                 │
        ┌────────┴────────┐
        ▼                 ▼
┌──────────────────┐  ┌──────────────────┐
│  LLM Provider    │  │  Data Sources    │
│                  │  │                  │
│  - OpenAI        │  │  - RAG Examples  │
│    (primary)     │  │  - Embeddings    │
│  - Anthropic     │  │  - Profiles      │
│    (fallback)    │  │  - Memory Store  │
└──────────────────┘  └──────────────────┘
```

---

## 2. Multi-Stage Decision Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                    DECISION PIPELINE                            │
└─────────────────────────────────────────────────────────────────┘

INPUT: User Profile + Context + Two Restaurant Cards

┌─────────────────────────────────┐
│ STEP 1: Data Preparation        │
│ ┌────────────────────────────┐  │
│ │ Load User Profile          │  │
│ │ - OCEAN traits (0-1)       │  │
│ │ - Demographics             │  │
│ │ - Derived preferences      │  │
│ └────────────────────────────┘  │
│            ▼                     │
│ ┌────────────────────────────┐  │
│ │ Prepare Context            │  │
│ │ - Current time & weather   │  │
│ │ - Is weekend?              │  │
│ │ - Temperature, rain        │  │
│ └────────────────────────────┘  │
│            ▼                     │
│ ┌────────────────────────────┐  │
│ │ Validate Cards             │  │
│ │ - Parse image data         │  │
│ │ - Type coercion            │  │
│ │ - Fill missing values       │  │
│ └────────────────────────────┘  │
└─────────────────────────────────┘
           ▼
┌─────────────────────────────────┐
│ STEP 2: RAG Retrieval           │
│ ┌────────────────────────────┐  │
│ │ Generate Query Embedding   │  │
│ │ (from profile + context)   │  │
│ │ 1536 dimensions            │  │
│ └────────────────────────────┘  │
│            ▼                     │
│ ┌────────────────────────────┐  │
│ │ Cosine Similarity Search   │  │
│ │ - Load 10K examples        │  │
│ │ - Compute similarity       │  │
│ │ - Return top 10 matches    │  │
│ └────────────────────────────┘  │
└─────────────────────────────────┘
           ▼
┌─────────────────────────────────────────┐
│ STEP 3: Build Comprehensive Prompt      │
│ ┌───────────────────────────────────┐   │
│ │ User Profile Section              │   │
│ │ - OCEAN traits with explanations  │   │
│ │ - Age, income, gender             │   │
│ │ - Derived preferences             │   │
│ └───────────────────────────────────┘   │
│ ┌───────────────────────────────────┐   │
│ │ Past Behavior Section             │   │
│ │ - 5-10 similar past decisions     │   │
│ │ - Context, choice, reasoning      │   │
│ └───────────────────────────────────┘   │
│ ┌───────────────────────────────────┐   │
│ │ Current Decision Section          │   │
│ │ - Card A details                  │   │
│ │ - Card B details                  │   │
│ │ - Current context summary         │   │
│ └───────────────────────────────────┘   │
│ ┌───────────────────────────────────┐   │
│ │ Personality Guidelines            │   │
│ │ - High openness → novel cuisines  │   │
│ │ - High conscientiousness → ratings│   │
│ │ - etc.                            │   │
│ └───────────────────────────────────┘   │
│ ┌───────────────────────────────────┐   │
│ │ Task Instructions                 │   │
│ │ - Output format: JSON             │   │
│ │ - Required fields                 │   │
│ └───────────────────────────────────┘   │
└─────────────────────────────────────────┘
           ▼
┌─────────────────────────────────────────┐
│ STAGE 1: THE DECIDER                    │
│ ┌───────────────────────────────────┐   │
│ │ LLM Generation                    │   │
│ │ - Model: GPT-4o-mini (or Claude)  │   │
│ │ - Temperature: 0.3                │   │
│ │ - Max tokens: 500                 │   │
│ │ - Prompt: As shown above          │   │
│ └───────────────────────────────────┘   │
│            ▼                            │
│ OUTPUT: Natural text response           │
│ "Based on my personality, I prefer...  │
│  The rating difference (4.7 vs 4.3)    │
│  is significant and matches my...       │
│  I'll choose A."                        │
└─────────────────────────────────────────┘
           ▼
┌─────────────────────────────────────────┐
│ STAGE 2: THE ANALYST                    │
│ ┌───────────────────────────────────┐   │
│ │ Parse & Structure Extraction      │   │
│ │ Prompt:                           │   │
│ │ "Extract JSON from the text above"│   │
│ │ Format:                           │   │
│ │ {                                 │   │
│ │   "choice": "A" or "B",           │   │
│ │   "confidence": 0.0-1.0,          │   │
│ │   "reasoning": "...",             │   │
│ │   "key_factors": [...]            │   │
│ │ }                                 │   │
│ └───────────────────────────────────┘   │
│            ▼                            │
│ │ LLM Extraction                    │   │
│ │ - Model: GPT-4o-mini              │   │
│ │ - Temperature: 0.1 (deterministic)│   │
│ │ - Max tokens: 300                 │   │
│ └───────────────────────────────────┘   │
│            ▼                            │
│ OUTPUT: Structured JSON                 │
│ {                                       │
│   "choice": "A",                        │
│   "confidence": 0.87,                   │
│   "reasoning": "Superior rating...",    │
│   "key_factors": ["rating", "novelty"] │
│ }                                       │
└─────────────────────────────────────────┘
           ▼
┌─────────────────────────────────────────┐
│ STEP 4: Build Result Dictionary         │
│                                         │
│ ┌──────────────────────────────────┐   │
│ │ Primary Outputs:                 │   │
│ │ - action: "A"                    │   │
│ │ - rationale: extracted reason    │   │
│ │ - confidence: 0.87               │   │
│ │ - key_factors: ["rating", ...]   │   │
│ └──────────────────────────────────┘   │
│                                         │
│ ┌──────────────────────────────────┐   │
│ │ Pipeline Metadata:               │   │
│ │ - full_prompt (for debugging)    │   │
│ │ - decider_response (raw text)    │   │
│ │ - analyst_extraction (raw JSON)  │   │
│ │ - extraction_status              │   │
│ └──────────────────────────────────┘   │
│                                         │
│ ┌──────────────────────────────────┐   │
│ │ Legacy Fields (None):            │   │
│ │ - prob_A, score_margin, drivers  │   │
│ └──────────────────────────────────┘   │
└─────────────────────────────────────────┘

OUTPUT: Complete decision result with explanation & confidence
```

---

## 3. Data Flow: RAG System

```
┌──────────────────────────────────────────────────────────┐
│           RAG (RETRIEVAL-AUGMENTED GENERATION)           │
└──────────────────────────────────────────────────────────┘

OFFLINE PHASE (One-time Setup):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Input: 300K training interactions (CSV)
   ▼
Generate User Profiles (1,000 synthetic users)
   ├─ Traits: openness, conscientiousness, extraversion, agreeableness, neuroticism
   ├─ Demographics: age, gender, income
   └─ Derived: novelty_seeking, budget_sensitivity, etc.
   ▼
Sample 10,000 diverse examples
   ├─ User personality
   ├─ Context (time, weather, day type)
   ├─ Restaurant card attributes (A vs B)
   └─ Decision + reasoning
   ▼
Convert to RAG JSON Format
   {
     "user_id": "USER_042",
     "ocean": {...},
     "context_summary": "19:00, weekday, 28°C",
     "decision": {"action": "A", "rationale_category": "rating"},
     "reasoning": "..."
   }
   ▼
Output: rag_examples.json (13 MB)
   ▼
Generate Embeddings (1536-dim vectors)
   ├─ Model: text-embedding-3-small
   ├─ Input: context + personality description
   └─ Cache: rag_embeddings.npy (117 MB)


ONLINE PHASE (Per Decision):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Current Twin Profile + Context
   │
   ├─ OCEAN traits: O=0.73, C=0.52, E=0.61, A=0.48, N=0.35
   ├─ Age, income, gender
   ├─ Current time, weather, location
   │
   ▼
Generate Query Embedding
   ├─ Format personality + context as text
   ├─ Call embedding API
   └─ Output: 1536-dim vector
   ▼
Load RAG Examples (10K examples in JSON)
   ▼
Load Cached Embeddings (1536-dim × 10K)
   ▼
Compute Cosine Similarity
   ├─ Similarity(query, example_1) = 0.92
   ├─ Similarity(query, example_2) = 0.88
   ├─ Similarity(query, example_3) = 0.85
   └─ ... (sort and select top 10)
   ▼
Return Top-10 Similar Past Decisions
   ├─ Example 1: USER_069, O=0.71 → Chose A (rating reason)
   ├─ Example 2: USER_045, O=0.75 → Chose B (novelty reason)
   └─ Example 3: USER_152, O=0.68 → Chose A (distance reason)
   ▼
Format for Prompt Injection
   ▼
## YOUR PAST BEHAVIOR
1. Similar context (O=0.71) → Chose A: "Better rating matched my adventurous side"
2. Similar context (O=0.75) → Chose B: "Novel cuisine despite higher price"
3. Similar context (O=0.68) → Chose A: "Rating consistency was key"
```

---

## 4. Component Interaction Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                  STREAMLIT UI (app_streamlit.py)             │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Welcome Step: Explain the experiment                 │   │
│  └────────────────────┬─────────────────────────────────┘   │
│                       │ Click: Start Experiment              │
│  ┌────────────────────▼─────────────────────────────────┐   │
│  │ Setup Step:                                          │   │
│  │ - Select city (default 8 Indian cities)              │   │
│  │ - Fetch weather (Open-Meteo API)                     │   │
│  │ - Upload Card A image                               │   │
│  │ - Upload Card B image                               │   │
│  └────────────────────┬─────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────────┐
│            CARD PARSER (twins/card_parser.py)               │
│                                                              │
│  For each card image:                                        │
│  1. Encode to base64                                         │
│  2. Call OpenAI Vision API                                   │
│  3. Extract: name, cuisine, price, rating, delivery_time    │
│  4. Validate (whitelist fields, type coercion)              │
│  5. Return structured data                                   │
└────────┬───────────────────────────────────────────────────┘
         │ Parsed Cards + Weather Context
         ▼
┌──────────────────────────────────────────────────────────────┐
│         TWIN RUNTIME (twins/twin_runtime.py)                │
│                                                              │
│  For each of ~10 twin profiles:                              │
│  1. Load profile from data/twin_profiles/USER_XXX.json       │
│  2. Prepare context (time, weather, demographics)            │
│  3. Call DecisionTool.choose()                               │
│  4. Store result in memory                                   │
└────────┬───────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────┐
│        DECISION TOOL (twins/tools.py)                        │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ RAG Retriever                                       │    │
│  │ - Get similar past decisions (k=10)                │    │
│  │ - Load from data/rag_examples.json                 │    │
│  │ - Use embeddings for similarity                    │    │
│  └────────────────┬────────────────────────────────────┘    │
│                   │ Top-10 similar examples                  │
│  ┌────────────────▼────────────────────────────────────┐    │
│  │ Prompt Builder (twins/prompts_llm.py)              │    │
│  │ - Build comprehensive decision prompt              │    │
│  │ - Include profile, context, cards, RAG examples    │    │
│  └────────────────┬────────────────────────────────────┘    │
│                   │ Full prompt string                       │
│  ┌────────────────▼────────────────────────────────────┐    │
│  │ Stage 1: The Decider (LLMClient)                   │    │
│  │ - Model: GPT-4o-mini (temp: 0.3)                   │    │
│  │ - Output: Natural text explanation                 │    │
│  └────────────────┬────────────────────────────────────┘    │
│                   │ Natural text response                    │
│  ┌────────────────▼────────────────────────────────────┐    │
│  │ Stage 2: The Analyst (LLMClient)                   │    │
│  │ - Extract JSON from Stage 1 output                 │    │
│  │ - Model: GPT-4o-mini (temp: 0.1)                   │    │
│  │ - Output: {choice, confidence, reasoning, factors} │    │
│  └────────────────┬────────────────────────────────────┘    │
│                   │ Structured result dict                   │
│  ┌────────────────▼────────────────────────────────────┐    │
│  │ Memory Store Integration                           │    │
│  │ - Record decision in memory_store.json             │    │
│  │ - Enable future retrieval                          │    │
│  └────────────────┬────────────────────────────────────┘    │
└────────┬──────────────────────────────────────────────────────┘
         │ Result: {action, rationale, confidence, key_factors}
         ▼
┌──────────────────────────────────────────────────────────────┐
│              RESULTS AGGREGATION                             │
│                                                              │
│  For all ~10 twin decisions:                                 │
│  1. Count votes (A vs B)                                     │
│  2. Extract top factors                                      │
│  3. Compute decision criteria breakdown                      │
│  4. Calculate average confidence                             │
│  5. Build results dashboard                                  │
└────────┬───────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────┐
│              STREAMLIT UI (Results Step)                     │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Results Dashboard:                                   │   │
│  │ - Vote counts (A: 7 twins, B: 3 twins)               │   │
│  │ - Top factors (rating, novelty, delivery_time)       │   │
│  │ - Decision breakdown chart                           │   │
│  │ - Expandable per-twin table with details             │   │
│  │ - Reset button for new experiment                    │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

---

## 5. File Dependency Graph

```
┌─ app_streamlit.py (Main UI)
│  │
│  ├─▶ twins/prompt_simulator.py
│  │   ├─▶ twins/twin_profile.py
│  │   ├─▶ twins/tools.py
│  │   └─▶ twins/prompts_llm.py
│  │
│  ├─▶ twins/card_parser.py
│  │   └─▶ twins/tools.py (LLMClient)
│  │
│  └─▶ twins/weather.py (Open-Meteo API)
│
├─ twins/twin_runtime.py
│  ├─▶ twins/twin_profile.py
│  ├─▶ twins/tools.py (DecisionTool)
│  └─▶ twins/memory_store.py
│
├─ twins/tools.py (Core decision engine)
│  ├─▶ twins/rag_retriever.py
│  │   └─▶ data/rag_examples.json
│  │   └─▶ data/rag_embeddings.npy
│  │
│  └─▶ twins/prompts_llm.py
│
├─ scripts/build_rag_examples.py
│  └─▶ data/train_expanded.csv → data/rag_examples.json
│
├─ scripts/generate_user_profiles.py
│  └─▶ data/twin_profiles/*.json
│
├─ scripts/generate_synth.py
│  ├─▶ data/twin_profiles/*.json
│  └─▶ data/train_expanded.csv / test_expanded.csv
│
└─ tests/
   ├─▶ test_end_to_end.py
   ├─▶ test_multi_stage.py
   └─▶ (all import from twins/)
```

---

## 6. Data Pipeline

```
┌─────────────────────────────────────────────────────────┐
│          SYNTHETIC DATA GENERATION PIPELINE             │
└─────────────────────────────────────────────────────────┘

STEP 1: Generate User Profiles
┌────────────────────────────────┐
│ generate_user_profiles.py       │
│                                │
│ Input: start_id, end_id        │
│ Output: 1,000 JSON files       │
│                                │
│ Each profile:                  │
│ {                              │
│   "user_id": "USER_001",       │
│   "name": "Alice",             │
│   "OCEAN": {                   │
│     "openness": 0.73,          │
│     "conscientiousness": 0.52, │
│     ...                        │
│   }                            │
│ }                              │
└────────┬───────────────────────┘
         │
         ▼ data/twin_profiles/
         │ USER_001.json ... USER_1000.json


STEP 2: Generate Synthetic Interactions
┌────────────────────────────────┐
│ generate_synth.py              │
│                                │
│ For each user:                 │
│ - Load profile                 │
│ - Generate 600 interactions    │
│ - Each interaction:            │
│   - Random context             │
│   - Random restaurant pair     │
│   - Personality-based choice   │
│   - Rationale category         │
│                                │
│ Output: CSV with 45 features   │
│ - Personality traits (5)       │
│ - Demographics (4)             │
│ - Context (4)                  │
│ - Card differences (8)         │
│ - Decision + rationale (2)     │
└────────┬───────────────────────┘
         │
         ▼ data/
         ├─ train_expanded.csv (300,600 rows)
         └─ test_expanded.csv (299,400 rows)


STEP 3: Build RAG Database
┌────────────────────────────────┐
│ build_rag_examples.py          │
│                                │
│ Input: train_expanded.csv      │
│ Sample: 10,000 diverse rows    │
│                                │
│ For each sample:               │
│ - Extract user profile         │
│ - Extract context summary      │
│ - Extract decision + reasoning │
│ - Format for RAG injection     │
│                                │
│ Output: JSON with structure:   │
│ {                              │
│   "user_id": "USER_042",       │
│   "ocean": {...},              │
│   "context_summary": "19:00...",
│   "decision": {...},           │
│   "reasoning": "..."           │
│ }                              │
└────────┬───────────────────────┘
         │
         ▼ data/
         └─ rag_examples.json (13 MB, 10K examples)


STEP 4: Generate Embeddings
┌────────────────────────────────┐
│ Embedding Generation           │
│ (triggered on first run)        │
│                                │
│ For each RAG example:          │
│ - Format as text prompt        │
│ - Call OpenAI embedding API    │
│ - Get 1536-dim vector          │
│                                │
│ Batch processing:              │
│ - 100 examples at a time       │
│ - Cache to disk                │
│ - Reuse on future runs         │
└────────┬───────────────────────┘
         │
         ▼ data/
         └─ rag_embeddings.npy (117 MB)


STEP 5: Validate Datasets
┌────────────────────────────────┐
│ validate_datasets.py           │
│                                │
│ Checks:                        │
│ - Missing values               │
│ - Data type consistency        │
│ - Value ranges                 │
│ - OCEAN trait distributions    │
│ - Decision balance (A vs B)    │
│                                │
│ Output: validation_report.json │
└─────────────────────────────────┘
```

---

## 7. API Call Sequence

```
USER MAKES A DECISION REQUEST

1. Streamlit UI
   └─▶ User uploads cards, selects city

2. Card Parser
   ├─▶ OpenAI Vision API (extract card data)
   └─▶ Return: {name, cuisine, rating, price, ...}

3. Weather Module
   ├─▶ Open-Meteo Geocoding API (validate location)
   ├─▶ Open-Meteo Forecast API (get weather)
   └─▶ Return: {temp_c, precip_mm, hour, is_weekend}

4. For Each Twin (repeat ~10 times):

   4a. RAG Retriever
       ├─▶ Generate embedding (local CPU or API)
       ├─▶ Load cached embeddings from disk
       ├─▶ Compute similarities (local CPU)
       └─▶ Return: top 10 similar decisions

   4b. Prompt Builder
       ├─▶ Build comprehensive prompt (local)
       └─▶ Return: full prompt string

   4c. Stage 1: The Decider
       ├─▶ OpenAI API (GPT-4o-mini)
       │   - Temperature: 0.3
       │   - Max tokens: 500
       │   - Prompt: comprehensive multi-section
       └─▶ Return: natural text (2-3 paragraphs)

   4d. Stage 2: The Analyst
       ├─▶ OpenAI API (GPT-4o-mini)
       │   - Temperature: 0.1
       │   - Max tokens: 300
       │   - Prompt: "Extract JSON from text above"
       └─▶ Return: JSON {choice, confidence, reasoning, factors}

   4e. Memory Store
       └─▶ Record decision locally

5. Results Aggregation (local)
   └─▶ Aggregate votes, factors, confidence

6. Streamlit UI
   └─▶ Display results dashboard

TOTAL API CALLS (PER DECISION):
- Vision API: 2 calls (2 cards)
- Weather API: 2 calls (geocoding + forecast)
- OpenAI LLM: ~20 calls (2 per twin × 10 twins)
  └─ 10 Decider calls + 10 Analyst calls
- Embedding: 1 call (if cache miss)

TYPICAL TIMING:
- Cards upload: <1s
- Weather fetch: <1s
- Per-twin decision: 0.3-0.4s
- 10 twins total: 3-4s
- Results display: instant

TOTAL LATENCY: 3-5 seconds per experiment
```

---

## 8. Error Handling Flow

```
┌──────────────────────────────────────────────────┐
│           ERROR HANDLING STRATEGY               │
└──────────────────────────────────────────────────┘

WEATHER API FAILURE
└─ fetch_current_weather()
   ├─ Attempt 1: Try API call
   │  └─ Failure → Attempt 2
   ├─ Attempt 2: Retry with backoff
   │  └─ Failure → Return defaults
   └─ Default fallback:
      {temp_c: 0, precip_mm: 0, error: True}
      (UI still functions with placeholder weather)


CARD PARSING FAILURE
└─ extract_from_image()
   ├─ Vision API fails → Return empty dict {}
   ├─ JSON parse fails → Try regex extraction
   └─ Validation fails → Return partial data
      (User can manually enter missing fields)


RAG RETRIEVAL FAILURE
└─ RAGRetriever.get_similar()
   ├─ Examples not found → Log warning, return []
   ├─ Embeddings not cached → Generate on-the-fly
   ├─ Similarity fails → Fall back to feature matching
   └─ Decider proceeds with no RAG context
      (Less personalized but still functional)


LLM PROVIDER FAILURE
└─ LLMClient.generate()
   ├─ No API key configured → Return ""
   ├─ API call fails → Return ""
   ├─ Invalid response format → Try parsing anyway
   └─ JSON parsing fails in Analyst:
      {
        "choice": "A",  # Default
        "confidence": 0.5,
        "reasoning": "Unable to extract",
        "key_factors": [],
        "extraction_status": "failed: JSONDecodeError"
      }


GRACEFUL DEGRADATION
User experiences:
├─ No weather → Uses 0°C as placeholder
├─ No card parsing → Manual entry form
├─ No RAG context → Still gets personalized decision
├─ No LLM response → Uses sensible defaults
└─ Partial failures → UI shows partial results + warnings

All failures logged, user informed via UI
```

---

**Generated**: November 10, 2025
**Diagrams Version**: 1.0
