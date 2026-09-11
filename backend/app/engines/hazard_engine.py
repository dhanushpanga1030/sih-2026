"""Hazard Engine — XGBoost/RF-based hazard scoring.

Computes flood and landslide susceptibility using trained ML models.
Falls back to deterministic rules if models aren't loaded.
"""

import pickle
from pathlib import Path

import numpy as np

MODEL_DIR = Path(__file__).parent.parent / "models"


class HazardEngine:
    def __init__(self):
        self.models = None
        self._load_models()

    def _load_models(self):
        fp = MODEL_DIR / "trained_models.pkl"
        if fp.exists():
            with open(fp, "rb") as f:
                self.models = pickle.load(f)

    def predict_flood(self, features: dict) -> dict:
        """Predict flood susceptibility score."""
        if self.models and "flood_model" in self.models:
            try:
                feature_vec = np.array([[features.get(k, 0) for k in self.models["feature_names"]]])
                score = float(self.models["flood_model"].predict(feature_vec)[0])
                confidence = self._estimate_confidence(features, "flood")
                return {
                    "score": round(min(max(score, 0), 1), 3),
                    "confidence": confidence,
                    "method": "xgboost",
                }
            except Exception:
                pass

        return self._fallback_flood(features)

    def predict_landslide(self, features: dict) -> dict:
        """Predict landslide susceptibility score."""
        if self.models and "landslide_model" in self.models:
            try:
                feature_vec = np.array([[features.get(k, 0) for k in self.models["feature_names"]]])
                score = float(self.models["landslide_model"].predict(feature_vec)[0])
                confidence = self._estimate_confidence(features, "landslide")
                return {
                    "score": round(min(max(score, 0), 1), 3),
                    "confidence": confidence,
                    "method": "random_forest",
                }
            except Exception:
                pass

        return self._fallback_landslide(features)

    def combine_hazard(
        self, flood: float, landslide: float, seismic: float, erosion: float
    ) -> dict:
        """Combine sub-hazard scores into overall hazard score."""
        combined = 0.35 * flood + 0.25 * landslide + 0.25 * seismic + 0.15 * erosion
        return {
            "combined": round(combined, 3),
            "flood": round(flood, 3),
            "landslide": round(landslide, 3),
            "seismic": round(seismic, 3),
            "erosion": round(erosion, 3),
        }

    def _estimate_confidence(self, features: dict, hazard_type: str) -> float:
        """Estimate model confidence based on feature completeness."""
        required_keys = {
            "flood": ["rainfall_mm", "river_dist_km", "slope", "flood_history"],
            "landslide": ["slope", "rainfall_mm", "landslide_history"],
        }
        keys = required_keys.get(hazard_type, [])
        present = sum(1 for k in keys if features.get(k, 0) != 0)
        base_confidence = 0.75
        completeness_bonus = (present / len(keys)) * 0.20 if keys else 0
        return round(base_confidence + completeness_bonus, 2)

    def _fallback_flood(self, features: dict) -> dict:
        """Deterministic fallback for flood scoring."""
        score = (
            0.3 * (features.get("rainfall_mm", 1500) / 3000)
            + 0.3 * (1 - min(features.get("river_dist_km", 10) / 20, 1))
            + 0.2 * (features.get("slope", 10) / 45)
            + 0.2 * features.get("flood_history", 0.3)
        )
        return {
            "score": round(min(max(score, 0), 1), 3),
            "confidence": 0.65,
            "method": "deterministic",
        }

    def _fallback_landslide(self, features: dict) -> dict:
        """Deterministic fallback for landslide scoring."""
        score = (
            0.4 * (features.get("slope", 10) / 45)
            + 0.3 * (features.get("rainfall_mm", 1500) / 3000)
            + 0.3 * features.get("landslide_history", 0.2)
        )
        return {
            "score": round(min(max(score, 0), 1), 3),
            "confidence": 0.65,
            "method": "deterministic",
        }


hazard_engine = HazardEngine()
