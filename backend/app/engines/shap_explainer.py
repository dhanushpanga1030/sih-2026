"""SHAP Explainability Engine for SafeHabitat AI.

Generates SHAP values for each model prediction to explain
which features contributed most to a risk classification.
"""
import pickle
import numpy as np
from pathlib import Path

MODEL_DIR = Path(__file__).parent.parent / "models"


class SHAPExplainer:
    def __init__(self):
        self.models = None
        self.shap_values = None
        self._load_models()

    def _load_models(self):
        fp = MODEL_DIR / "trained_models.pkl"
        if fp.exists():
            with open(fp, "rb") as f:
                self.models = pickle.load(f)

    def explain_hazard(self, features: dict) -> dict:
        """Get feature contributions for hazard prediction."""
        if not self.models:
            return self._fallback_explanation(features)

        try:
            import shap
            model = self.models["flood_model"]
            feature_vec = np.array([[features.get(k, 0) for k in self.models["feature_names"]]])
            explainer = shap.TreeExplainer(model)
            shap_vals = explainer.shap_values(feature_vec)[0]

            contributions = {}
            for i, name in enumerate(self.models["feature_names"]):
                contributions[name] = round(float(shap_vals[i]), 4)

            sorted_contribs = sorted(contributions.items(), key=lambda x: abs(x[1]), reverse=True)
            return {
                "contributions": dict(sorted_contribs),
                "top_positive": [k for k, v in sorted_contribs if v > 0][:3],
                "top_negative": [k for k, v in sorted_contribs if v < 0][:3],
                "base_value": round(float(explainer.expected_value), 4) if hasattr(explainer, 'expected_value') else 0,
            }
        except ImportError:
            return self._fallback_explanation(features)

    def explain_risk(self, features: dict) -> dict:
        """Get feature contributions for overall risk prediction."""
        if not self.models:
            return self._fallback_risk_explanation(features)

        try:
            import shap
            model = self.models["risk_model"]
            feature_vec = np.array([[features.get(k, 0) for k in self.models["feature_names"]]])
            explainer = shap.TreeExplainer(model)
            shap_vals = explainer.shap_values(feature_vec)[0]

            contributions = {}
            for i, name in enumerate(self.models["feature_names"]):
                contributions[name] = round(float(shap_vals[i]), 4)

            sorted_contribs = sorted(contributions.items(), key=lambda x: abs(x[1]), reverse=True)
            return {
                "contributions": dict(sorted_contribs),
                "top_factors": [k for k, v in sorted_contribs[:5]],
                "base_value": round(float(explainer.expected_value), 4) if hasattr(explainer, 'expected_value') else 0,
            }
        except ImportError:
            return self._fallback_risk_explanation(features)

    def _fallback_explanation(self, features: dict) -> dict:
        """Rule-based fallback when SHAP is unavailable."""
        contribs = {
            "rainfall_mm": round(features.get("rainfall_mm", 0) / 3000 * 0.3, 4),
            "river_dist_km": round((1 - min(features.get("river_dist_km", 10) / 20, 1)) * 0.3, 4),
            "slope": round(features.get("slope", 0) / 45 * 0.2, 4),
            "flood_history": round(features.get("flood_history", 0) * 0.2, 4),
        }
        sorted_c = sorted(contribs.items(), key=lambda x: x[1], reverse=True)
        return {
            "contributions": dict(sorted_c),
            "top_positive": [k for k, _ in sorted_c[:3]],
            "top_negative": [],
            "base_value": 0.15,
            "method": "rule-based fallback",
        }

    def _fallback_risk_explanation(self, features: dict) -> dict:
        """Rule-based fallback for risk explanation."""
        contribs = {
            "flood_history": round(features.get("flood_history", 0) * 0.35, 4),
            "landslide_history": round(features.get("landslide_history", 0) * 0.25, 4),
            "poverty_index": round(features.get("poverty_index", 0) * 0.15, 4),
            "infra_quality": round((1 - features.get("infra_quality", 0.5)) * 0.15, 4),
            "population": round(min(features.get("population", 1000) / 5000, 1) * 0.10, 4),
        }
        sorted_c = sorted(contribs.items(), key=lambda x: x[1], reverse=True)
        return {
            "contributions": dict(sorted_c),
            "top_factors": [k for k, _ in sorted_c[:5]],
            "base_value": 0.10,
            "method": "rule-based fallback",
        }


explainer = SHAPExplainer()
