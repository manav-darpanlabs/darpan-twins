# Darpan Twins Lab - Digital Twin Decision-Making Platform

**AI-Powered Digital Twin Experiments for Food Delivery Preferences**

Last Updated: November 8, 2025

---

## Overview

Darpan Twins Lab is an **LLM-based digital twin platform** that simulates food delivery decision-making based on OCEAN personality traits. The system uses **Retrieval-Augmented Generation (RAG)** and a **multi-stage LLM pipeline** to generate personality-driven restaurant choices without requiring traditional machine learning training.

### Key Features

- **Pure LLM Architecture**: No ML models required - all decisions via prompt engineering
- **Multi-Stage Pipeline**: Natural text generation (The Decider) + structured extraction (The Analyst)
- **RAG-Based Context**: 10,000 past decisions provide contextual examples
- **Personality-Driven**: OCEAN traits influence decisions naturally
- **Instant Deployment**: No training required, just configure and run
- **Production Ready**: Comprehensive testing, validation, and documentation

---

## Quick Start

### 1. Prerequisites

- Python 3.9+
- OpenAI API key (or Anthropic API key)
- 2GB RAM minimum
- Internet connection

### 2. Installation

```bash
# Clone repository and navigate to project
cd /path/to/p1

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API key
# Required:
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
OPENAI_API_KEY=sk-...

# Optional (defaults provided):
RAG_EXAMPLES_PATH=data/rag_examples.json
RAG_EMBEDDING_CACHE=data/rag_embeddings.npy
RAG_K_NEIGHBORS=10
```

### 4. Generate RAG Database (First Time Only)

```bash
python scripts/build_rag_examples.py \
  --input data/train_expanded.csv \
  --output data/rag_examples.json \
  --max_examples 10000 \
  --seed 42
```

**Output**: Creates `data/rag_examples.json` (13 MB, 10,000 examples)

### 5. Run the Application

```bash
streamlit run app_streamlit.py
```

**Access**: Open browser to http://localhost:8501

---

## How It Works

### The Multi-Stage LLM Pipeline

```
User Profile + Restaurant Cards
          ↓
    RAG Retrieval (find similar past decisions)
          ↓
    Stage 1: The Decider (natural text explanation)
          ↓
    Stage 2: The Analyst (extract structured data)
          ↓
    Decision: A or B + confidence + reasoning
```

### The Agents

1. **🎭 The Decider** - Generates personality-driven natural text explanations
   - Input: User traits, cards, RAG examples
   - Output: 2-3 paragraph natural explanation
   - Temperature: 0.3 (balanced)

2. **🔬 The Analyst** - Extracts structured data from text
   - Input: Decider's natural text
   - Output: JSON {choice, confidence, reasoning, factors}
   - Temperature: 0.1 (deterministic)

---

## Project Structure

```
p1/
├── README.md                    # This file
├── app_streamlit.py            # Main Streamlit application
├── .env.example                # Environment template
├── .env                        # Your configuration (not in git)
├── requirements.txt            # Python dependencies
│
├── twins/                      # Core digital twin logic
│   ├── tools.py               # DecisionTool (multi-stage pipeline)
│   ├── rag_retriever.py       # RAG similarity search
│   ├── prompts_llm.py         # Prompt builders
│   ├── twin_runtime.py        # High-level API
│   ├── twin_profile.py        # User profile management
│   ├── memory_store.py        # Decision history
│   └── weather.py             # Weather API integration
│
├── data/
│   ├── rag_examples.json      # 10K past decisions (13 MB)
│   ├── rag_embeddings.npy     # Cached embeddings (117 MB)
│   ├── twin_profiles/         # 1,000 user profiles
│   ├── train_expanded.csv     # Training data (300K rows)
│   └── test_expanded.csv      # Test data (300K rows)
│
├── scripts/
│   ├── generate_synth.py              # Generate synthetic data
│   ├── generate_user_profiles.py     # Create user profiles
│   ├── build_rag_examples.py         # Build RAG database
│   ├── test_llm_consistency.py       # Consistency tests
│   └── test_personality_alignment.py # Personality tests
│
├── docs/
│   ├── ARCHITECTURE.md        # Complete architecture guide
│   ├── DEPLOYMENT.md          # Deployment guide
│   ├── DATA_GENERATION.md     # Synthetic data documentation
│   └── archive/               # Historical documentation
│
└── tests/
    ├── test_end_to_end.py     # E2E tests
    └── test_multi_stage.py    # Pipeline tests
```

---

## Usage Guide

### Using the Streamlit App

#### Step 1: Location & Context
1. Select city from dropdown (Mumbai, Delhi, Bangalore, etc.)
2. Weather automatically fetches and displays
3. Or search custom city if needed

#### Step 2: Upload Restaurant Cards
1. Upload Card A image (screenshot of restaurant option)
2. Upload Card B image
3. Preview images to verify upload
4. View parsed data (name, cuisine, price, rating, etc.)
5. Click "Start Experiment"

#### Step 3: View Results
- **Aggregate Results**: See how many twins chose A vs B
- **Top Factors**: Most common decision reasons
- **Decision Criteria**: Breakdown by price, delivery, fit, trust
- **Detailed Data**: Per-twin breakdown in expandable table
- **Reset**: Click "Run Another Experiment" to restart

### Programmatic Usage

```python
from twins.twin_runtime import TwinRuntime

# Load user profile
twin = TwinRuntime.from_profile_path("data/twin_profiles/USER_042.json")

# Define restaurant cards
card_a = {
    "name": "Sushi Express",
    "cuisine": "sushi",
    "rating_avg": 4.7,
    "dish_price": 450,
    "delivery_time_min": 35,
    "distance_km": 4.2,
    # ... other attributes
}

card_b = {
    "name": "Pizza Palace",
    "cuisine": "pizza",
    "rating_avg": 4.3,
    "dish_price": 280,
    # ... other attributes
}

# Context
context = {
    "hour_of_day": 19,
    "is_weekend": 0,
    "temperature_c": 28,
    "precip_mm": 0.0
}

# Make decision
result = twin.choose_between_cards(card_a, card_b, context)

# Access results
print(f"Choice: {result['action']}")  # "A" or "B"
print(f"Reasoning: {result['rationale']}")
print(f"Confidence: {result['meta']['confidence']}")
print(f"Factors: {result['meta']['key_factors']}")

# Access multi-stage outputs (optional)
print(f"Decider: {result['meta']['decider_response']}")
print(f"Analyst: {result['meta']['analyst_extraction']}")
```

---

## Testing

### Run All Tests

```bash
# Consistency test (same input → same output?)
python scripts/test_llm_consistency.py --user_id USER_001 --runs 10

# Personality alignment (high-O → novel cuisine?)
python scripts/test_personality_alignment.py --users 20

# End-to-end integration tests
python test_end_to_end.py

# Pipeline structure tests (no API key needed)
python test_multi_stage.py
```

### Expected Results

- **Consistency**: >80% (typically 85-90%)
- **Personality Alignment**: High-openness users choose novel cuisines more often
- **Latency**: 3-4 seconds per decision
- **Cost**: ~$0.003 per decision

---

## Data Generation

### User Profiles

1,000 synthetic user profiles with:
- **OCEAN Traits**: Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism
- **Demographics**: Age (18-65), Gender, Income (₹100K-₹5M)
- **Derived Preferences**: Novelty seeking, budget sensitivity, etc.

**Generate new profiles**:
```bash
python scripts/generate_user_profiles.py \
  --output_dir data/twin_profiles \
  --start_id 1001 \
  --end_id 2000 \
  --seed 42
```

### Synthetic Interactions

600,000 restaurant choice interactions:
- **Training set**: 300,600 rows (501 users × 600 interactions)
- **Test set**: 299,400 rows (499 users × 600 interactions)
- **Features**: 45 per row (traits, context, card differences)

**Generate interactions**:
```bash
python scripts/generate_synth.py \
  --output data/train_expanded.csv \
  --profile_dir data/twin_profiles \
  --user_range "USER_001:USER_500" \
  --interactions_per_user 600 \
  --seed 42
```

---

## Performance Metrics

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| **Consistency** | >80% | 85-90% | ✅ |
| **Latency** | <5s | 3-4s | ✅ |
| **Cost** | <$0.01 | $0.003 | ✅ |
| **Personality Alignment** | Yes | Confirmed | ✅ |
| **Extraction Success** | >90% | 100% | ✅ |

---

## Architecture Highlights

### No Training Required
- Pure LLM approach - no XGBoost, no scikit-learn
- Instant deployment - just configure API keys
- Updates via prompt engineering, not retraining

### RAG-Based Learning
- 10,000 past decisions provide context
- Semantic similarity search via embeddings
- Soft learning without gradient updates

### Multi-Stage Pipeline
- Stage 1 (Decider): Natural personality-driven text
- Stage 2 (Analyst): Structured data extraction
- Robust fallback mechanisms

### Production Ready
- Comprehensive test suite
- Error handling and retries
- Backward compatible APIs
- Full documentation

---

## Documentation

- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Complete architecture guide
  - RAG system details
  - Multi-stage pipeline
  - Migration from ML to LLM
  - Testing and validation

- **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Deployment guide
  - Environment setup
  - Configuration options
  - Production checklist

- **[docs/DATA_GENERATION.md](docs/DATA_GENERATION.md)** - Data documentation
  - Synthetic data generation
  - User profile creation
  - Validation reports

- **[docs/archive/](docs/archive/)** - Historical documentation
  - UI changes history
  - Bug fixes summary

---

## Requirements

### Python Dependencies

```
openai >= 1.12.0          # OpenAI API
anthropic >= 0.36.0       # Anthropic API (optional)
pandas >= 2.0.0           # Data manipulation
numpy >= 1.24.0           # Numerical operations
streamlit >= 1.30.0       # Web UI
python-dotenv >= 1.0.0    # Environment variables
```

### System Requirements

- Python 3.9 or higher
- 2GB RAM minimum (4GB recommended)
- Internet connection (for LLM APIs)
- ~250 MB disk space for data

---

## Troubleshooting

### Issue: No RAG examples found

**Solution**:
```bash
python scripts/build_rag_examples.py --input data/train_expanded.csv
```

### Issue: Weather shows 0°C

**Solution**: Check internet connection and weather API. System uses fallback values if API fails.

### Issue: API key errors

**Solution**:
1. Verify `.env` file exists
2. Check `OPENAI_API_KEY` is set correctly
3. Test: `echo $OPENAI_API_KEY`

### Issue: Low consistency (<80%)

**Solutions**:
- Lower temperature in `.env` (try 0.2 instead of 0.3)
- Test with users with clear trait extremes
- Review prompt clarity

---

## Development

### Running in Development Mode

```bash
# Activate virtual environment
source .venv/bin/activate

# Run with live reload
streamlit run app_streamlit.py --server.runOnSave true

# View logs
tail -f ~/.streamlit/logs/streamlit.log
```

### Running Tests During Development

```bash
# Quick structure test (no API key needed)
python test_multi_stage.py

# Full integration tests (requires API key)
python test_end_to_end.py

# Watch mode (re-run on file changes)
ls twins/*.py | entr python test_multi_stage.py
```

---

## Contributing

This is a research prototype. For questions or suggestions:

1. Review documentation in `docs/`
2. Check test scripts for examples
3. Verify `.env` configuration
4. Run validation scripts

---

## Architecture Version

**Current**: v3.1 (Multi-Stage LLM Pipeline with RAG)
**Status**: ✅ Production Ready
**Last Updated**: November 8, 2025

---

## License

[Add your license information here]

---

## Contact

For questions about the architecture, implementation, or deployment:
- Review comprehensive docs in `docs/ARCHITECTURE.md`
- Check deployment guide in `docs/DEPLOYMENT.md`
- Run test scripts to verify setup
- Inspect `.env.example` for configuration options

---

## Acknowledgments

Built with:
- OpenAI GPT-4o-mini for LLM inference
- Streamlit for web interface
- RAG architecture for contextual learning
- Synthetic OCEAN personality data for training examples
