import os
from typing import Dict, List, Tuple

import joblib
import numpy as np


FEATURE_NAMES_FALLBACK: List[str] = [
    "diff_dish_price",
    "diff_delivery_time_min",
    "diff_distance_km",
    "diff_delivery_fee",
    "diff_rating_avg",
    "diff_num_reviews",
    "diff_coupon_available",
    "diff_sponsored",
    "diff_cuisine_italian",
    "diff_cuisine_mexican",
    "diff_cuisine_sushi",
    "diff_cuisine_indian",
    "diff_cuisine_american",
    "diff_cuisine_chinese",
    "diff_cuisine_thai",
    "diff_cuisine_pizza",
    "diff_cuisine_burgers",
    # context
    "hour_of_day",
    "is_weekend",
    "temperature_c",
    "precip_mm",
    # personality
    "ctx_openness",
    "ctx_conscientiousness",
    "ctx_extraversion",
    "ctx_agreeableness",
    "ctx_neuroticism",
    "ctx_novelty_seeking",
    "ctx_budget_sensitivity",
    "ctx_distance_tolerance",
    "ctx_rating_focus",
    # demographics
    "dem_age",
    "dem_income",
    "dem_pob_avg_income",
    "dem_pob_food_variety_index",
    "dem_gender_male",
    "dem_gender_female",
    "dem_gender_other",
]


class PolicyModel:
    def __init__(self, model_dir: str = "models") -> None:
        self.model_dir = model_dir
        self.model = None
        self.scaler = None
        self.feature_names: List[str] = FEATURE_NAMES_FALLBACK
        # rationale head (optional)
        self.rationale_pipe = None
        self.rationale_feature_names: List[str] = []
        self._load()

    def _load(self) -> None:
        features_path = os.path.join(self.model_dir, "feature_names.pkl")
        scaler_path = os.path.join(self.model_dir, "scaler.pkl")
        model_path = os.path.join(self.model_dir, "click_model.pkl")
        rationale_path = os.path.join(self.model_dir, "rationale_pipeline.pkl")
        rationale_feats_path = os.path.join(self.model_dir, "rationale_feature_names.pkl")

        if os.path.exists(features_path):
            try:
                self.feature_names = joblib.load(features_path)
            except Exception:
                self.feature_names = FEATURE_NAMES_FALLBACK

        if os.path.exists(scaler_path):
            try:
                self.scaler = joblib.load(scaler_path)
            except Exception:
                self.scaler = None

        if os.path.exists(model_path):
            try:
                self.model = joblib.load(model_path)
            except Exception:
                self.model = None
        if os.path.exists(rationale_path):
            try:
                self.rationale_pipe = joblib.load(rationale_path)
            except Exception:
                self.rationale_pipe = None
        if os.path.exists(rationale_feats_path):
            try:
                self.rationale_feature_names = joblib.load(rationale_feats_path)
            except Exception:
                self.rationale_feature_names = []

    @staticmethod
    def _diff_features(card_a: Dict[str, float], card_b: Dict[str, float]) -> Dict[str, float]:
        def get(key: str) -> float:
            return float(card_a.get(key, 0.0) - card_b.get(key, 0.0))

        cuisines = [
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
        feats: Dict[str, float] = {
            "diff_dish_price": get("dish_price"),
            "diff_delivery_time_min": get("delivery_time_min"),
            "diff_distance_km": get("distance_km"),
            "diff_delivery_fee": get("delivery_fee"),
            "diff_rating_avg": get("rating_avg"),
            "diff_num_reviews": get("num_reviews"),
            "diff_coupon_available": get("coupon_available"),
            "diff_sponsored": get("sponsored"),
        }
        for c in cuisines:
            feats[f"diff_cuisine_{c}"] = get(f"cuisine_{c}")
        return feats

    @staticmethod
    def _context_features(context: Dict[str, float]) -> Dict[str, float]:
        return {
            # context
            "hour_of_day": float(context.get("hour_of_day", 13)),
            "is_weekend": float(context.get("is_weekend", 0)),
            "temperature_c": float(context.get("temperature_c", 24.0)),
            "precip_mm": float(context.get("precip_mm", 0.0)),
            # personality
            "ctx_openness": float(context.get("openness", context.get("ctx_openness", 0.5))),
            "ctx_conscientiousness": float(
                context.get("conscientiousness", context.get("ctx_conscientiousness", 0.5))
            ),
            "ctx_extraversion": float(
                context.get("extraversion", context.get("ctx_extraversion", 0.5))
            ),
            "ctx_agreeableness": float(
                context.get("agreeableness", context.get("ctx_agreeableness", 0.5))
            ),
            "ctx_neuroticism": float(context.get("neuroticism", context.get("ctx_neuroticism", 0.5))),
            "ctx_novelty_seeking": float(context.get("novelty_seeking", context.get("ctx_novelty_seeking", 0.5))),
            "ctx_budget_sensitivity": float(
                context.get("budget_sensitivity", context.get("ctx_budget_sensitivity", 0.5))
            ),
            "ctx_distance_tolerance": float(
                context.get("distance_tolerance", context.get("ctx_distance_tolerance", 0.5))
            ),
            "ctx_rating_focus": float(context.get("rating_focus", context.get("ctx_rating_focus", 0.5))),
            # demographics (pass-through if provided)
            "dem_age": float(context.get("dem_age", 30)),
            "dem_income": float(context.get("dem_income", 60000.0)),
            "dem_pob_avg_income": float(context.get("dem_pob_avg_income", 50000.0)),
            "dem_pob_food_variety_index": float(context.get("dem_pob_food_variety_index", 0.6)),
            "dem_gender_male": float(context.get("dem_gender_male", 0.0)),
            "dem_gender_female": float(context.get("dem_gender_female", 0.0)),
            "dem_gender_other": float(context.get("dem_gender_other", 0.0)),
        }

    def _build_feature_vector(
        self, card_a: Dict[str, float], card_b: Dict[str, float], context: Dict[str, float]
    ) -> np.ndarray:
        feats = {}
        feats.update(self._diff_features(card_a, card_b))
        feats.update(self._context_features(context))
        x = np.array([feats.get(name, 0.0) for name in self.feature_names], dtype=float)
        return x

    def predict_action(
        self, card_a: Dict[str, float], card_b: Dict[str, float], context: Dict[str, float]
    ) -> Dict[str, object]:
        x = self._build_feature_vector(card_a, card_b, context)
        if self.scaler is not None:
            x_scaled = self.scaler.transform([x])[0]
        else:
            x_scaled = x

        if self.model is not None and hasattr(self.model, "predict_proba"):
            proba = float(self.model.predict_proba([x_scaled])[0][1])
            coef = getattr(self.model, "coef_", None)
            if coef is not None:
                coef_vec = coef[0]
            else:
                coef_vec = np.zeros_like(x_scaled)
        else:
            # Fallback heuristic
            weights = np.zeros_like(x_scaled)
            for key, w in {
                "diff_rating_avg": 1.0,
                "diff_dish_price": -0.8,
                "diff_distance_km": -0.6,
                "diff_delivery_time_min": -0.5,
                "diff_coupon_available": 0.4,
            }.items():
                try:
                    idx = self.feature_names.index(key)
                    weights[idx] = w
                except ValueError:
                    pass
            score = float(np.dot(weights, x_scaled))
            proba = float(1 / (1 + np.exp(-score)))
            coef_vec = weights

        action = "A" if proba >= 0.5 else "B"
        score_margin = float(abs(proba - 0.5) * 2)

        contributions = x_scaled * coef_vec
        top_idx = np.argsort(np.abs(contributions))[::-1][:6]
        drivers: List[Tuple[str, float]] = [
            (self.feature_names[i], float(contributions[i])) for i in top_idx
        ]

        out = {
            "action": action,
            "prob_A": proba,
            "score_margin": score_margin,
            "drivers": drivers,
        }
        # optional rationale label prediction
        if self.rationale_pipe is not None and self.rationale_feature_names:
            xr = np.array([context.get(name, 0.0) if not name.startswith("diff_") else (card_a.get(name.replace("diff_", ""), 0.0) - card_b.get(name.replace("diff_", ""), 0.0)) for name in self.rationale_feature_names], dtype=float)
            try:
                label = self.rationale_pipe.predict([xr])[0]
                out["rationale_label_pred"] = str(label)
            except Exception:
                pass
        return out
