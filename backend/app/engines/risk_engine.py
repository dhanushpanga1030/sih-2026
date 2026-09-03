"""Risk Fusion Engine — Combines hazard, exposure, vulnerability into overall risk.

Uses trained XGBoost model for fusion when available.
"""
import pickle
import numpy as np
from pathlib import Path

MODEL_DIR = Path(__file__).parent.parent / "models"


class RiskEngine:
    def __init__(self):
        self.models = None
        self._load_models()

    def _load_models(self):
        fp = MODEL_DIR / "trained_models.pkl"
        if fp.exists():
            with open(fp, "rb") as f:
                self.models = pickle.load(f)

    def compute_risk(self, hazard: float, exposure: float, vulnerability: float,
                     features: dict = None) -> dict:
        """Compute overall risk score and priority band."""
        if self.models and "risk_model" in self.models and features:
            try:
                feature_vec = np.array([[features.get(k, 0) for k in self.models["feature_names"]]])
                risk_score = float(self.models["risk_model"].predict(feature_vec)[0])
                risk_score = round(min(max(risk_score, 0), 1), 3)
                confidence = self._estimate_confidence(features)
            except Exception:
                risk_score = self._weighted_risk(hazard, exposure, vulnerability)
                confidence = 0.65
        else:
            risk_score = self._weighted_risk(hazard, exposure, vulnerability)
            confidence = 0.65

        band = self._classify_band(risk_score)

        return {
            "overall_risk": risk_score,
            "band": band,
            "hazard_score": round(hazard, 3),
            "exposure_score": round(exposure, 3),
            "vulnerability_score": round(vulnerability, 3),
            "confidence": confidence,
            "contributing_factors": self._contributing_factors(hazard, exposure, vulnerability, features),
        }

    def _weighted_risk(self, hazard: float, exposure: float, vulnerability: float) -> float:
        """Deterministic weighted risk fusion."""
        return round(0.4 * hazard + 0.3 * exposure + 0.3 * vulnerability, 3)

    def _classify_band(self, risk: float) -> str:
        """Classify risk into priority band."""
        if risk >= 0.65:
            return "immediate"
        elif risk >= 0.50:
            return "short_term"
        elif risk >= 0.35:
            return "medium_term"
        else:
            return "monitor"

    def _contributing_factors(self, hazard: float, exposure: float,
                               vulnerability: float, features: dict = None) -> dict:
        """Decompose risk into contributing factor weights."""
        base = {
            "hazard_contribution": round(0.4 * hazard, 4),
            "exposure_contribution": round(0.3 * exposure, 4),
            "vulnerability_contribution": round(0.3 * vulnerability, 4),
        }
        if features:
            base["flood_risk"] = round(features.get("flood_history", 0) * 0.35, 4)
            base["seismic_risk"] = round(features.get("seismic_zone", 5) * 0.05, 4)
            base["landslide_risk"] = round(features.get("landslide_history", 0) * 0.25, 4)
            base["poverty_impact"] = round(features.get("poverty_index", 0) * 0.15, 4)
            base["infrastructure_gap"] = round((1 - features.get("infra_quality", 0.5)) * 0.15, 4)
        return base

    def _estimate_confidence(self, features: dict) -> float:
        """Estimate confidence from feature completeness."""
        key_features = ["flood_history", "landslide_history", "poverty_index",
                        "infra_quality", "population", "rainfall_mm"]
        present = sum(1 for k in key_features if features.get(k) is not None)
        return round(0.70 + (present / len(key_features)) * 0.25, 2)


risk_engine = RiskEngine()
