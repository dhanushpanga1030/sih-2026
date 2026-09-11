"""Data Drift Monitoring for SafeHabitat AI.

Tracks model performance degradation and data distribution shifts.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent.parent / "data"
DRIFT_LOG = DATA_DIR / "drift_monitoring.json"


@dataclass
class DriftAlert:
    timestamp: str
    alert_type: str  # distribution_shift, model_degradation, data_staleness
    severity: str  # low, medium, high, critical
    feature: str
    message: str
    details: dict


class DriftMonitor:
    def __init__(self):
        self.alerts: list[DriftAlert] = []
        self.baselines: dict = {}
        self._load_baselines()

    def _load_baselines(self):
        baseline_path = DATA_DIR / "drift_baselines.json"
        if baseline_path.exists():
            with open(baseline_path) as f:
                self.baselines = json.load(f)

    def check_distribution(
        self, feature_name: str, current_values: list[float]
    ) -> DriftAlert | None:
        """Check if current data distribution has shifted from baseline."""
        baseline = self.baselines.get(feature_name)
        if not baseline:
            return None

        import statistics

        current_mean = statistics.mean(current_values)
        current_std = statistics.stdev(current_values) if len(current_values) > 1 else 0

        baseline_mean = baseline.get("mean", 0)
        baseline_std = baseline.get("std", 1)

        mean_shift = abs(current_mean - baseline_mean) / baseline_std if baseline_std > 0 else 0

        if mean_shift > 2:
            severity = "high" if mean_shift > 3 else "medium"
            alert = DriftAlert(
                timestamp=datetime.now().isoformat(),
                alert_type="distribution_shift",
                severity=severity,
                feature=feature_name,
                message=f"{feature_name} mean shifted {mean_shift:.1f} std deviations",
                details={
                    "baseline_mean": baseline_mean,
                    "current_mean": current_mean,
                    "baseline_std": baseline_std,
                    "current_std": current_std,
                },
            )
            self.alerts.append(alert)
            return alert
        return None

    def check_data_freshness(
        self, source: str, last_updated: str, max_age_days: int = 30
    ) -> DriftAlert | None:
        """Check if data source has become stale."""
        last_dt = datetime.fromisoformat(last_updated.replace("Z", "+00:00"))
        age = datetime.now() - last_dt.replace(tzinfo=None)

        if age.days > max_age_days:
            severity = "high" if age.days > max_age_days * 2 else "medium"
            alert = DriftAlert(
                timestamp=datetime.now().isoformat(),
                alert_type="data_staleness",
                severity=severity,
                feature=source,
                message=f"{source} data is {age.days} days old (max {max_age_days})",
                details={"last_updated": last_updated, "age_days": age.days},
            )
            self.alerts.append(alert)
            return alert
        return None

    def check_model_performance(
        self, model_name: str, accuracy: float, baseline_accuracy: float
    ) -> DriftAlert | None:
        """Check if model accuracy has degraded."""
        degradation = baseline_accuracy - accuracy
        if degradation > 0.05:
            severity = (
                "critical" if degradation > 0.15 else "high" if degradation > 0.10 else "medium"
            )
            alert = DriftAlert(
                timestamp=datetime.now().isoformat(),
                alert_type="model_degradation",
                severity=severity,
                feature=model_name,
                message=f"{model_name} accuracy dropped {degradation:.1%} (from {baseline_accuracy:.1%} to {accuracy:.1%})",
                details={"baseline_accuracy": baseline_accuracy, "current_accuracy": accuracy},
            )
            self.alerts.append(alert)
            return alert
        return None

    def get_alerts(self, severity: str | None = None) -> list[dict]:
        alerts = self.alerts
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        return [a.__dict__ for a in alerts]

    def save_alerts(self):
        with open(DRIFT_LOG, "w") as f:
            json.dump(self.get_alerts(), f, indent=2)


monitor = DriftMonitor()
