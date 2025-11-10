# DARPAN TWINS LAB - COMPREHENSIVE CODEBASE ANALYSIS

**Project**: Digital Twin Decision-Making Platform for Food Delivery
**Status**: Production Ready (v3.1)
**Last Updated**: November 8, 2025
**Current Branch**: v1_am (with unsaved changes to app_streamlit.py)

---

## 1. PROJECT OVERVIEW

### Core Concept
Darpan Twins Lab is an **LLM-based digital twin platform** that simulates food delivery decision-making using:
- OCEAN personality traits (Big Five model)
- Retrieval-Augmented Generation (RAG) with 10,000 past decisions
- Multi-stage LLM pipeline (Decider → Analyst)
- No traditional ML models - pure LLM architecture

### Key Innovation
**Pure LLM Approach**: Replaces traditional ML-based decision trees with:
1. Comprehensive personality-driven prompts
2. Contextual RAG examples for consistency
3. Multi-stage processing for structured output
4. Instant deployment without training

### Target Use Case
Simulate how food delivery customers with different personalities choose between restaurant options based on context (time, weather, location).

---

## 2. PROJECT STRUCTURE

### Directory Layout

```
p1/
├── README.md                           # Comprehensive user guide
├── QUICK_START.md                      # Setup instructions
├── requirements.txt                    # Python dependencies
├── .env                                # Configuration (not in git)
├── .env.example                        # Configuration template
├── .gitignore                          # Git exclusions
├── app_streamlit.py                    # Main web application (1,448 lines)
├── cards.json                          # Sample restaurant cards
├── demo_agent_pipeline.py              # Example usage script
│
├── twins/                              # Core digital twin logic (1,909 LOC)
│   ├── __init__.py
│   ├── tools.py                        # DecisionTool & LLMClient (335 lines)
│   ├── rag_retriever.py               # RAG similarity search (268 lines)
│   ├── prompts_llm.py                 # Decision prompt builders (335 lines)
│   ├── twin_runtime.py                # High-level API (91 lines)
│   ├── twin_profile.py                # User profile management (70 lines)
│   ├── memory_store.py                # Decision history (56 lines)
│   ├── card_parser.py                 # Vision-based card extraction (100 lines)
│   ├── prompt_simulator.py            # Legacy simulator (457 lines)
│   ├── weather.py                     # Weather API integration (90 lines)
│   └── prompts.py                     # Legacy prompts (107 lines)
│
├── data/                               # Data and models (250+ MB)
│   ├── rag_examples.json              # 10,000 past decisions (13 MB)
│   ├── rag_embeddings.npy             # Cached embeddings (117 MB)
│   ├── train_expanded.csv             # Training data (123 MB, 300K rows)
│   ├── test_expanded.csv              # Test data (123 MB, 300K rows)
│   ├── memory_store.json              # Decision history (7.6 KB)
│   ├── rationale_bank.json            # Decision rationale templates
│   ├── validation_report.json          # Data validation results
│   ├── choices.csv                    # Historical choices (1.9 MB)
│   └── twin_profiles/                 # User profiles (1,000 JSON files)
│       ├── USER_001.json
│       ├── USER_002.json
│       └── ... (1,000 total)
│
├── scripts/                            # Data generation & validation
│   ├── build_rag_examples.py          # CSV → RAG JSON converter
│   ├── generate_synth.py              # Synthetic data generator
│   ├── generate_user_profiles.py      # User profile generator
│   ├── validate_datasets.py           # Data validation suite
│   └── extract_cards.py               # Card extraction utility
│
├── tests/                              # Test suite
│   ├── test_end_to_end.py             # E2E integration tests
│   ├── test_multi_stage.py            # Pipeline structure tests
│   ├── test_llm_consistency.py        # Consistency validation
│   ├── test_personality_alignment.py  # Personality behavior tests
│   ├── test_weather_fix.py            # Weather API tests
│   ├── test_app_changes.py            # App UI/UX tests
│   └── validate_app.py                # App validation
│
├── docs/                               # Comprehensive documentation
│   ├── ARCHITECTURE.md                # Technical architecture (19.6 KB)
│   ├── DEPLOYMENT.md                  # Deployment guide (14.4 KB)
│   ├── DATA_GENERATION.md             # Synthetic data docs (10.8 KB)
│   ├── DOCUMENTATION_CONSOLIDATION.md # Doc updates (8.5 KB)
│   └── archive/                       # Historical documentation
│
├── config/
│   └── .streamlit/
│       └── config.toml                # Streamlit configuration
│
├── web/                                # Frontend (React + TypeScript)
│   ├── package.json                   # Dependencies
│   ├── tsconfig.json                  # TypeScript config
│   ├── src/
│   └── node_modules/                  # 500+ packages
│
├── models/                             # Model directory (placeholder)
│   └── .gitkeep                        # No actual ML models
│
└── .claude/                            # Claude development config
    └── settings.local.json
```

---

## 3. TECHNOLOGY STACK

### Backend
- **Language**: Python 3.9+
- **Web Framework**: Streamlit 1.30.0
- **LLM Clients**: OpenAI (1.12.0+) & Anthropic (0.36.0+)
- **Data Processing**: pandas 2.0.0+, numpy 1.24.0+
- **Configuration**: python-dotenv 1.0.0+

### Frontend
- **Framework**: React 18.2.0
- **Language**: TypeScript 5.6.3
- **Build Tool**: Vite 5.4.8
- **Styling**: Tailwind CSS 3.4.14
- **Routing**: React Router DOM 6.28.0
- **Charts**: Recharts 2.12.7 (data visualization)
- **Icons**: Lucide React 0.460.0

### External APIs
- **LLM**: OpenAI GPT-4o-mini (primary) or Anthropic Claude (fallback)
- **Weather**: Open-Meteo API (free, no auth)
- **Geocoding**: Open-Meteo Geocoding API
- **Vision**: OpenAI Vision API (card parsing)

### Data Storage
- **Examples**: JSON (10,000 examples, 13 MB)
- **Embeddings**: NumPy binary format (117 MB)
- **Profiles**: JSON files (1,000 users)
- **Training Data**: CSV (300K+ rows each)
- **Memory**: In-memory JSON (local persistence)

---

## 4. MAIN COMPONENTS & RESPONSIBILITIES

### 4.1 Core Decision-Making Pipeline

#### DecisionTool (twins/tools.py)
**Purpose**: Orchestrates multi-stage LLM decision-making

**Key Methods**:
- `choose()` - Main entry point for decision-making
  - Retrieves similar past decisions via RAG
  - Calls The Decider for natural text explanation
  - Calls The Analyst for structured extraction
  - Returns combined result dict
- `_call_decider()` - Stage 1: Natural language generation (temp=0.3)
- `_call_analyst()` - Stage 2: JSON extraction (temp=0.1)

**Responsibilities**:
- Multi-stage LLM orchestration
- RAG retrieval management
- Response parsing and validation
- Backward compatibility interface

**Critical Data Flow**:
```
User Profile + Context + Cards
  ↓
RAG Similarity Search (k=10)
  ↓
Build Comprehensive Prompt
  ↓
Stage 1: The Decider (natural text, temp=0.3)
  ↓
Stage 2: The Analyst (JSON extraction, temp=0.1)
  ↓
Structured Output {action, confidence, reasoning, key_factors}
```

#### LLMClient (twins/tools.py)
**Purpose**: Unified interface to multiple LLM providers

**Providers Supported**:
- OpenAI (GPT-4o-mini, GPT-4, etc.)
- Anthropic (Claude 3.5, etc.)

**Key Methods**:
- `generate()` - Text generation with temperature control
- `generate_vision()` - Vision API for restaurant card parsing

**Configuration**:
- Loads from `.env` file
- Falls back gracefully if provider unavailable
- Supports both old and new OpenAI SDK versions

### 4.2 RAG System

#### RAGRetriever (twins/rag_retriever.py)
**Purpose**: Retrieves contextually similar past decisions

**Data Sources**:
- Examples: `data/rag_examples.json` (10,000 examples)
- Embeddings: `data/rag_embeddings.npy` (cached 1536-dim vectors)

**Key Methods**:
- `get_similar()` - Returns k most similar past decisions
- `_load_examples()` - Loads JSON example database
- `_load_or_generate_embeddings()` - Manages embedding cache
- `_get_embedding()` - Generates embeddings via OpenAI API

**Similarity Matching**:
- Uses cosine similarity on embeddings
- Embedding model: `text-embedding-3-small` (1536 dimensions)
- Falls back to feature-based matching if embeddings unavailable
- Caches embeddings to disk for performance

**Example Usage in Prompt**:
The retrieved examples are formatted as:
```
## YOUR PAST BEHAVIOR
1. Similar context → Chose X: [reasoning]
2. Similar context → Chose Y: [reasoning]
...
```

### 4.3 User Profile Management

#### TwinProfile (twins/twin_profile.py)
**Purpose**: Encapsulates user personality and preferences

**Core Attributes**:
- OCEAN traits (0-1 normalized):
  - `openness` (adventurousness, creativity)
  - `conscientiousness` (organization, carefulness)
  - `extraversion` (sociability, outgoingness)
  - `agreeableness` (compassion, cooperation)
  - `neuroticism` (anxiety, sensitivity)

**Key Methods**:
- `from_json()` - Load profile from JSON file
- `to_context()` - Derive contextual preferences from traits
- `style_tokens()` - Compute personality-driven writing style
- `greeting()` - Generate persona-appropriate greeting

**Derived Preferences** (computed from OCEAN):
```python
novelty_seeking = 0.7 * openness + 0.3 * (1 - conscientiousness)
budget_sensitivity = 0.5 * (1 - conscientiousness) + 0.5 * neuroticism
distance_tolerance = 0.6 * extraversion + 0.2 * openness - 0.3 * neuroticism
rating_focus = 0.4 * agreeableness + 0.6 * conscientiousness
```

#### TwinRuntime (twins/twin_runtime.py)
**Purpose**: High-level API for making decisions with a twin

**Key Methods**:
- `choose_between_cards()` - Decision entry point
- `from_profile_path()` - Factory constructor

**Responsibilities**:
- Profile loading and context management
- Memory store integration
- DecisionTool orchestration

### 4.4 Prompt Engineering

#### Prompt Builders (twins/prompts_llm.py)
**Purpose**: Dynamically generates decision prompts

**Key Functions**:

1. `build_decider_prompt()`
   - Input: User name, OCEAN traits, demographics, context, cards, RAG examples
   - Output: Comprehensive prompt for natural text decision-making
   - Structure:
     - User profile section
     - Past behavior (RAG examples)
     - Current decision options
     - Personality-driven guidelines
     - Task instructions
   - Temperature: 0.3 (balanced consistency with natural variation)

2. `build_analyst_prompt()`
   - Input: The Decider's natural text response
   - Output: Prompt to extract structured JSON
   - Enforces format: `{choice, confidence, reasoning, key_factors}`
   - Temperature: 0.1 (deterministic)

**Personality-Driven Guidance**:
Dynamically generated based on trait levels:
```
High Openness (>0.7):
  • Novel cuisines strongly appeal
  • Willing to try new places
  
High Conscientiousness (>0.7):
  • Ratings matter a lot
  • Reviews are important
  
High Neuroticism (>0.7):
  • High ratings reduce anxiety
  • Prefer established restaurants
```

### 4.5 Data Pipeline

#### Data Generation (scripts/)

1. **generate_user_profiles.py**
   - Generates synthetic OCEAN personality profiles
   - Output: 1,000 JSON files in `data/twin_profiles/`
   - Fields: user_id, OCEAN traits, name, demographics

2. **generate_synth.py**
   - Generates synthetic restaurant choice interactions
   - Uses profiles × contexts × card pairs
   - Output: CSV with 45 features per row
   - Splits: 300K training + 300K testing rows
   - Features include: personality, demographics, context, card attributes, choice

3. **build_rag_examples.py**
   - Converts CSV → RAG-ready JSON format
   - Samples 10,000 diverse examples
   - Adds reasoning and context summaries
   - Output: `data/rag_examples.json` (13 MB)

4. **validate_datasets.py**
   - Validates data integrity and distributions
   - Checks for missing values, outliers
   - Generates validation report

#### Card Parser (twins/card_parser.py)
**Purpose**: Extract restaurant data from uploaded images

**Key Functions**:
- `extract_from_image()` - Uses OpenAI Vision API
- `build_vision_prompt()` - Generates extraction schema
- `validate_card()` - Whitelists and type-coerces fields

**Extracted Fields**:
- name, cuisine, dish_price
- delivery_time_min, distance_km, delivery_fee
- rating_avg, num_reviews
- coupon_text, sponsored (0/1)

### 4.6 Decision History

#### MemoryStore (twins/memory_store.py)
**Purpose**: Persists decision history for each user

**Key Methods**:
- `append()` - Record new decision
- `retrieve()` - Find similar past decisions by context
- Jaccard similarity matching on tokenized context

**Data Format**:
```json
{
  "user_id": "USER_042",
  "context_summary": "19:00, weekday, 28°C",
  "action": "A",
  "rationale": "Better rating matches personality"
}
```

### 4.7 Weather Integration

#### Weather Module (twins/weather.py)
**Purpose**: Fetch real-time weather for context

**APIs Used**:
- Open-Meteo Forecast (free, no auth)
- Open-Meteo Geocoding

**Key Functions**:
- `search_cities()` - Geocode location
- `fetch_current_weather()` - Get current conditions
  - Temperature, precipitation, hour, is_weekend
  - Retry logic with fallback defaults
  - Returns: temp_c, precip_mm, error flags

---

## 5. MAIN APPLICATION (Streamlit)

### File: app_streamlit.py (1,448 lines)

#### Key Sections

1. **Imports & Setup** (lines 1-30)
   - Streamlit configuration
   - Theme styling and CSS
   - Default cities for quick selection

2. **Styling** (lines 35-515)
   - Dark theme with neon green/blue accents
   - CSS variables for consistency
   - Component-specific styles (buttons, panels, weather, cards)
   - Responsive layout system

3. **Helper Functions** (lines 527-743)
   - `parse_card_form()` - Extract uploaded card data
   - `format_factor()` - Format decision rationale text
   - `aggregate_results()` - Summarize twin decisions
   - `context_controls()` - Weather/time/location UI
   - `reset_experiment()` - Reset session state

4. **Main Application** (lines 758-1448)
   - **Welcome Step**: Onboarding and explanation
   - **Setup Step**: Location selection and card upload
   - **Running Step**: Progress bar for LLM calls
   - **Results Step**: Aggregated analysis and per-twin breakdown

#### Data Flow

```
User Input (Location + Cards)
  ↓
Parse Cards (vision extraction)
  ↓
Fetch Weather
  ↓
Load Twin Profiles (random selection from 1,000)
  ↓
For Each Twin:
  - Call DecisionTool.choose()
  - Store result
  ↓
Aggregate Results:
  - Vote counts (A vs B)
  - Top factors across twins
  - Decision criteria breakdown
  ↓
Display Results Dashboard
```

#### UI Components

1. **Header**: Logo, title, tagline with gradient effect
2. **Stepper**: Shows progress (Welcome → Setup → Running → Results)
3. **Weather Widget**: Real-time conditions with icons
4. **Card Upload**: Drag-and-drop image upload with preview
5. **Results Dashboard**:
   - Aggregate vote counts
   - Top factors (word cloud style)
   - Decision breakdown chart
   - Detailed per-twin table

#### Recent Changes (Uncommitted)
- Fixed weather container overflow issues
- Removed JavaScript label removal script (now using CSS)
- Changed "City & Upload" label to "Setup" in stepper
- Improved responsive behavior for mobile devices

---

## 6. DATA STRUCTURES

### User Profile (JSON)
```json
{
  "user_id": "USER_042",
  "name": "Alice",
  "OCEAN": {
    "openness": 0.73,
    "conscientiousness": 0.52,
    "extraversion": 0.61,
    "agreeableness": 0.48,
    "neuroticism": 0.35
  }
}
```

### Restaurant Card
```json
{
  "name": "Sushi Express",
  "cuisine": "sushi",
  "rating_avg": 4.7,
  "num_reviews": 2350,
  "dish_price": 450,
  "delivery_time_min": 35,
  "distance_km": 4.2,
  "delivery_fee": 40,
  "coupon_text": "FLAT50",
  "sponsored": 0
}
```

### Decision Result (Internal)
```python
{
  "action": "A",  # or "B"
  "rationale": "Better rating (4.7 vs 4.3) matches my adventurous personality",
  "confidence": 0.85,  # 0.0-1.0
  "key_factors": ["rating", "cuisine_novelty", "personality_fit"],
  
  # Pipeline metadata
  "prompt": "...",  # Full prompt sent
  "decider_response": "...",  # Stage 1 output
  "analyst_extraction": {...},  # Stage 2 output
  "agent_pipeline": {
    "stage_1": "The Decider",
    "stage_2": "The Analyst",
    "extraction_status": "success"
  },
  
  # Legacy fields (None)
  "prob_A": None,
  "score_margin": None,
  "drivers": []
}
```

### RAG Example
```json
{
  "user_id": "USER_069",
  "ocean": {...},
  "demographics": {...},
  "context_summary": "19:00, weekday, 28°C",
  "decision": {
    "action": "A",
    "rationale_category": "rating"
  },
  "reasoning": "Chose A: Card A has better rating, matching my adventurous nature"
}
```

---

## 7. TESTING STRATEGY

### Test Files

1. **test_end_to_end.py**
   - Full pipeline integration with real API calls
   - Tests decision output format and consistency
   - Validates confidence scores

2. **test_multi_stage.py**
   - Pipeline structure tests (no API key needed)
   - Validates prompt generation
   - Tests JSON parsing

3. **test_llm_consistency.py**
   - Same input → same output (>80% expected)
   - Measures decision stability
   - Tests with varied personality profiles

4. **test_personality_alignment.py**
   - High-openness → novel cuisines
   - High-conscientiousness → better ratings
   - Validates personality-driven behavior

5. **test_weather_fix.py**
   - Weather API error handling
   - Fallback behavior validation

### Performance Metrics

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Consistency | >80% | 85-90% | ✅ |
| Latency | <5s | 3-4s | ✅ |
| Cost | <$0.01 | $0.003 | ✅ |
| Personality Alignment | Yes | Confirmed | ✅ |
| Extraction Success | >90% | 100% | ✅ |

---

## 8. ARCHITECTURE INSIGHTS

### Design Decisions

1. **No ML Models**
   - Avoids need for training/retraining
   - Personality captured through prompt engineering
   - Instant deployment without infrastructure

2. **Multi-Stage Pipeline**
   - Stage 1 (Decider): Natural personality-driven text
   - Stage 2 (Analyst): Deterministic JSON extraction
   - Separation enables robust error handling

3. **RAG over Fine-Tuning**
   - 10K examples provide soft context learning
   - No gradient updates needed
   - Easy to update by adding new examples

4. **Temperature Strategy**
   - Decider: 0.3 (balanced creativity + consistency)
   - Analyst: 0.1 (deterministic parsing)
   - Yields 85-90% consistency while maintaining natural variation

5. **Backward Compatibility**
   - Dual LLM provider support (OpenAI + Anthropic)
   - Legacy fields preserved in output
   - Old SDK version compatibility

### Strengths

1. **Personality-Driven**: OCEAN traits naturally influence decisions
2. **Explainable**: Natural language reasoning for each decision
3. **Consistent**: 85-90% consistency within acceptable variance
4. **Scalable**: No model retraining needed for new personalities
5. **Fast**: 3-4 second decisions (competitive with ML)
6. **Low-Cost**: ~$0.003 per decision vs expensive fine-tuning

### Areas for Improvement

1. **Embedding Cache Size**: 117 MB embeddings file could be optimized
2. **RAG Coverage**: 10K examples may miss edge cases
3. **Prompt Fragility**: Changes to prompt format require re-testing
4. **No Active Learning**: Doesn't improve from real user feedback
5. **Limited Context Depth**: Could include more historical patterns
6. **API Dependencies**: No offline capability

---

## 9. KEY FILES SUMMARY

### Critical Production Files

| File | Lines | Purpose |
|------|-------|---------|
| `app_streamlit.py` | 1,448 | Main web application |
| `twins/tools.py` | 335 | LLM + RAG orchestration |
| `twins/rag_retriever.py` | 268 | Similarity search |
| `twins/prompts_llm.py` | 335 | Prompt generation |
| `twins/twin_runtime.py` | 91 | High-level API |
| `twins/twin_profile.py` | 70 | Profile management |

### Configuration Files

| File | Purpose |
|------|---------|
| `.env` | API keys (not in git) |
| `.env.example` | Configuration template |
| `config/.streamlit/config.toml` | Streamlit settings |
| `web/tsconfig.json` | TypeScript configuration |
| `requirements.txt` | Python dependencies |
| `web/package.json` | Node.js dependencies |

### Data Files

| File | Size | Purpose |
|------|------|---------|
| `data/rag_examples.json` | 13 MB | 10K past decisions |
| `data/rag_embeddings.npy` | 117 MB | Cached embeddings |
| `data/train_expanded.csv` | 123 MB | Training data (300K rows) |
| `data/test_expanded.csv` | 123 MB | Test data (300K rows) |
| `data/twin_profiles/` | ~1 MB | 1,000 user profiles |

---

## 10. DEVELOPMENT & DEPLOYMENT

### Setup

```bash
# Create environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env and add API key
```

### Running the Application

```bash
# Start Streamlit app
streamlit run app_streamlit.py

# Live reload (development)
streamlit run app_streamlit.py --server.runOnSave true
```

### Building RAG Database (First Time)

```bash
python scripts/build_rag_examples.py \
  --input data/train_expanded.csv \
  --output data/rag_examples.json \
  --max_examples 10000
```

### Testing

```bash
# Structure tests (no API key)
python tests/test_multi_stage.py

# Full integration tests
python tests/test_end_to_end.py

# Consistency validation
python scripts/test_llm_consistency.py --user_id USER_001 --runs 10

# Personality alignment
python scripts/test_personality_alignment.py --users 20
```

### Deployment Checklist

- [ ] Verify `.env` has correct API keys
- [ ] Check `data/rag_examples.json` exists (13 MB)
- [ ] Run test suite (target: all pass)
- [ ] Test with 5+ twin profiles
- [ ] Validate weather API works
- [ ] Check Streamlit responsive design
- [ ] Verify logging/monitoring
- [ ] Document custom configurations

---

## 11. CURRENT STATE

### Git Status
- **Branch**: v1_am (working on improvements)
- **Uncommitted Changes**: `app_streamlit.py`
  - Fixed weather container overflow
  - Removed JavaScript label removal script
  - Updated UI labels and styling

### Recent Commits
1. `16432ef7` - Project cleanup and reorganization: Phase 5-7 completion
2. `cd1e6ab3` - Major LLM migration and UI enhancements
3. `84d65670` - Add .venv/ to .gitignore
4. `7a0b6ee7` - chore: add .gitignore
5. `e49b9e17` - chore: initial commit

### Known Issues & TODOs

1. **JavaScript Cleanup**: Removed inline script, pure CSS now handles label hiding
2. **Responsive Design**: Recent fixes for mobile weather display
3. **Data Size**: RAG embeddings file (117 MB) could be optimized
4. **Missing Features**:
   - No A/B testing framework for prompt optimization
   - No feedback loop for improvement
   - No multi-language support
   - No offline mode

---

## 12. NOTABLE PATTERNS & CONVENTIONS

### Code Style
- Type hints throughout (strict mypy compliance)
- Docstrings for all major functions
- No comments - self-documenting code
- Early returns, no nested conditionals

### Error Handling
- Graceful fallbacks (weather API, LLM provider)
- Try-except with specific error types
- Warning messages for missing resources
- Validation before processing

### Data Validation
- Whitelist approach (card_parser)
- Type coercion with defaults
- Range normalization (0-1 for traits)
- Schema validation at trust boundaries

### Performance Optimizations
- Embedding caching to disk
- RAG retrieval K-NN efficiency
- Streamlit session state management
- Generator patterns in data processing

---

## 13. DOCUMENTATION STRUCTURE

### docs/ Directory
- **ARCHITECTURE.md** (19.6 KB)
  - Complete system architecture
  - RAG details, pipeline walkthrough
  - ML-to-LLM migration notes

- **DEPLOYMENT.md** (14.4 KB)
  - Environment setup
  - Configuration options
  - Production checklist

- **DATA_GENERATION.md** (10.8 KB)
  - Synthetic data process
  - User profile creation
  - Validation reports

- **archive/** (historical)
  - UI changes history
  - Bug fixes
  - Legacy implementation notes

---

## 14. SUMMARY TABLE

| Aspect | Details |
|--------|---------|
| **Language** | Python 3.9+, TypeScript, React |
| **Total LOC** | ~1,900 (twins) + 1,448 (app) |
| **Data Size** | 250+ MB (embeddings, CSVs, profiles) |
| **Dependencies** | 6 core Python + 9+ Node.js |
| **Test Coverage** | 6 test files covering all major paths |
| **API Calls** | OpenAI/Anthropic, Open-Meteo, Vision |
| **Deployment** | Streamlit (single-command) |
| **Performance** | 3-4s latency, $0.003/decision |
| **Consistency** | 85-90% same-input same-output |
| **Status** | Production Ready (v3.1) |

---

## 15. GETTING STARTED FOR DEVELOPERS

### Understanding the Flow
1. Read `README.md` for overview
2. Check `docs/ARCHITECTURE.md` for technical details
3. Review `twins/tools.py` for core logic
4. Examine `app_streamlit.py` for UI implementation
5. Run tests to see it in action

### Making Changes
1. Modify relevant module in `twins/`
2. Add corresponding test case
3. Run test suite: `python tests/test_*.py`
4. Test UI: `streamlit run app_streamlit.py`
5. Commit with clear message

### Key Entry Points
- **For decisions**: `TwinRuntime.choose_between_cards()`
- **For UI**: `main()` function in `app_streamlit.py`
- **For data**: Scripts in `scripts/` directory
- **For profiles**: Load from `data/twin_profiles/`

---

**End of Analysis**
