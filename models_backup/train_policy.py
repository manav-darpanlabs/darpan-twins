import argparse
import os
from typing import List, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

try:
    from xgboost import XGBClassifier  # type: ignore
    HAS_XGB = True
except Exception:
    HAS_XGB = False
from sklearn.neural_network import MLPClassifier
from sklearn.calibration import CalibratedClassifierCV


CONTEXT_FEATURES = [
    "hour_of_day",
    "is_weekend",
    "temperature_c",
    "precip_mm",
    # weather_code will be one-hot encoded; keep numeric features only for simplicity in MVP
]

PERSONALITY_FEATURES = [
    "ctx_openness",
    "ctx_conscientiousness",
    "ctx_extraversion",
    "ctx_agreeableness",
    "ctx_neuroticism",
    "ctx_novelty_seeking",
    "ctx_budget_sensitivity",
    "ctx_distance_tolerance",
    "ctx_rating_focus",
]

# Pairwise diffs from the generator schema
DIFF_FEATURES = [
    "diff_dish_price",
    "diff_delivery_time_min",
    "diff_distance_km",
    "diff_delivery_fee",
    "diff_rating_avg",
    "diff_num_reviews",
    "diff_coupon_available",
    "diff_sponsored",
    # cuisines will be included dynamically if present
]

CUISINES = [
    "italian",
    "mexican",
    "sushi",
    "indian",
    "american",
    "chinese",
    "thai",
    "pizza",
    "burgers",
]

# Demographics features
DEMOGRAPHICS = [
    "dem_age",
    "dem_income",
    "dem_pob_avg_income",
    "dem_pob_food_variety_index",
    "dem_gender_male",
    "dem_gender_female",
    "dem_gender_other",
]


def build_feature_list(df: pd.DataFrame) -> List[str]:
    features: List[str] = []

    # Add diffs that exist
    for f in DIFF_FEATURES:
        if f in df.columns:
            features.append(f)

    # Add cuisine diffs if exist
    for c in CUISINES:
        col = f"diff_cuisine_{c}"
        if col in df.columns:
            features.append(col)

    # Context numeric
    for f in CONTEXT_FEATURES:
        if f in df.columns:
            features.append(f)

    # Personality
    for f in PERSONALITY_FEATURES:
        if f in df.columns:
            features.append(f)

    # Demographics
    for f in DEMOGRAPHICS:
        if f in df.columns:
            features.append(f)

    return features


def load_data(csv_path: str) -> Tuple[pd.DataFrame, pd.Series, List[str]]:
    df = pd.read_csv(csv_path)

    # Convert booleans if any lurking
    if "action" not in df.columns:
        raise ValueError("Expected 'action' column with labels 'A' or 'B'.")

    y = (df["action"].astype(str) == "A").astype(int)

    feature_names = build_feature_list(df)
    X = df[feature_names].copy()

    return X, y, feature_names


def load_rationale_data(csv_path: str) -> Tuple[pd.DataFrame, pd.Series, List[str]]:
    df = pd.read_csv(csv_path)
    if "rationale_label" not in df.columns:
        raise ValueError("Expected 'rationale_label' column. Regenerate data.")
    X, _, feature_names = load_data(csv_path)
    y = df["rationale_label"].astype(str)
    return X, y, feature_names


def train_model(csv_path: str, model_dir: str, estimator: str = "xgb") -> None:
    os.makedirs(model_dir, exist_ok=True)

    X, y, feature_names = load_data(csv_path)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=17, stratify=y
    )

    numeric_features = feature_names
    preprocessor = ColumnTransformer(
        transformers=[("num", StandardScaler(), numeric_features)],
        remainder="drop",
    )

    est = estimator.lower()
    if est == "xgb" and HAS_XGB:
        model = XGBClassifier(
            n_estimators=300,
            max_depth=5,
            learning_rate=0.08,
            subsample=0.9,
            colsample_bytree=0.9,
            reg_lambda=1.0,
            objective="binary:logistic",
            eval_metric="logloss",
            n_jobs=2,
        )
        # XGB handles numeric scales, but we keep scaler for stable pipeline
        base_pipe = Pipeline(steps=[("pre", preprocessor), ("clf", model)])
        pipe = base_pipe
    elif est == "mlp":
        model = MLPClassifier(hidden_layer_sizes=(64, 32), activation="relu", early_stopping=True, max_iter=200)
        pipe = Pipeline(steps=[("pre", preprocessor), ("clf", model)])
    else:
        model = LogisticRegression(max_iter=1000, class_weight="balanced")
        pipe = Pipeline(steps=[("pre", preprocessor), ("clf", model)])

    pipe.fit(X_train, y_train)

    y_pred = pipe.predict(X_test)
    report = classification_report(y_test, y_pred, digits=3)
    print(report)

    # Persist artifacts
    joblib.dump(pipe, os.path.join(model_dir, "policy_pipeline.pkl"))

    # Extract fitted scaler and model
    fitted_scaler: StandardScaler = pipe.named_steps["pre"].named_transformers_["num"]
    fitted_model = pipe.named_steps["clf"]

    joblib.dump(fitted_scaler, os.path.join(model_dir, "scaler.pkl"))
    joblib.dump(fitted_model, os.path.join(model_dir, "click_model.pkl"))

    # Save feature names used for inference
    joblib.dump(feature_names, os.path.join(model_dir, "feature_names.pkl"))


def train_rationale(csv_path: str, model_dir: str, estimator: str = "xgb") -> None:
    os.makedirs(model_dir, exist_ok=True)
    X, y, feature_names = load_rationale_data(csv_path)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=19, stratify=y)

    numeric_features = feature_names
    preprocessor = ColumnTransformer(
        transformers=[("num", StandardScaler(), numeric_features)],
        remainder="drop",
    )

    est = estimator.lower()
    if est == "xgb" and HAS_XGB:
        model = XGBClassifier(
            n_estimators=300,
            max_depth=5,
            learning_rate=0.08,
            subsample=0.9,
            colsample_bytree=0.9,
            reg_lambda=1.0,
            objective="multi:softprob",
            eval_metric="mlogloss",
            n_jobs=2,
        )
        pipe = Pipeline(steps=[("pre", preprocessor), ("clf", model)])
    elif est == "mlp":
        model = MLPClassifier(hidden_layer_sizes=(128, 64), activation="relu", early_stopping=True, max_iter=300)
        pipe = Pipeline(steps=[("pre", preprocessor), ("clf", model)])
    else:
        # multinomial logistic regression
        model = LogisticRegression(max_iter=1000, class_weight=None, multi_class="multinomial")
        pipe = Pipeline(steps=[("pre", preprocessor), ("clf", model)])

    pipe.fit(X_train, y_train)
    y_pred = pipe.predict(X_test)
    print("Rationale classification report:\n", classification_report(y_test, y_pred, digits=3))

    joblib.dump(pipe, os.path.join(model_dir, "rationale_pipeline.pkl"))
    joblib.dump(feature_names, os.path.join(model_dir, "rationale_feature_names.pkl"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Train policy model on synthetic CAR data (extended schema)")
    parser.add_argument("--data", type=str, default="data/choices.csv")
    parser.add_argument("--model_dir", type=str, default="models")
    parser.add_argument("--estimator", type=str, default="xgb", choices=["xgb", "mlp", "logit"]) 
    parser.add_argument("--train_rationale", action="store_true", help="Also train rationale label classifier")
    args = parser.parse_args()

    train_model(csv_path=args.data, model_dir=args.model_dir, estimator=args.estimator)
    if args.train_rationale:
        train_rationale(csv_path=args.data, model_dir=args.model_dir, estimator=args.estimator)


if __name__ == "__main__":
    main()
