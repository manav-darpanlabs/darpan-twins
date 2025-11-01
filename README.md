## Run

1) Install deps
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

2) Generate synthetic data (with demographics)
```bash
python scripts/generate_synth.py --output data/choices.csv --profile_dir data/twin_profiles --interactions_per_user 600 --seed 33
```

3) Train policy (xgb/mlp/logit)
```bash
python scripts/train_policy.py --data data/choices.csv --model_dir models --estimator xgb
```

4) Set GPT env and run UI
```bash
echo "LLM_PROVIDER=openai" >> .env
echo "LLM_MODEL=gpt-4o-mini" >> .env
echo "OPENAI_API_KEY=sk-..." >> .env
streamlit run app_streamlit.py
```

The UI lets you pick a profile, set demographics/context, input two cards, and optionally ask an LLM to also choose an action. The twin uses the structured model for the decision and GPT for a short rationale.