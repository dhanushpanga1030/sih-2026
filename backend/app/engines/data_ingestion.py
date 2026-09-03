"""Data Ingestion Pipeline for SafeHabitat AI.

Handles loading and normalizing geospatial data from multiple formats:
- GeoJSON, Shapefile, CSV with lat/long, GeoTIFF metadata
- Integrates with the ML engines for scoring
"""
import json
import csv
from pathlib import Path
from datetime import datetime

DATA_DIR = Path(__file__).parent.parent.parent / "data"


class DataIngestionPipeline:
    """Ingest and normalize hazard, population, and infrastructure data."""

    SCHEMA = {
        "habitations": ["name", "district", "lat", "lon", "population", "area_sq_km"],
        "hazard_layers": ["elevation", "slope", "rainfall_mm", "river_dist_km", "flood_history", "landslide_history"],
        "vulnerability_layers": ["poverty_index", "age_vulnerability", "disability_index", "infra_quality"],
        "infrastructure": ["road_dist_km", "healthcare_dist_km", "school_dist_km", "water_availability"],
    }

    def __init__(self):
        self.sources_log = []

    def ingest_geojson(self, filepath: str, layer_type: str) -> list:
        """Ingest GeoJSON file and extract features."""
        with open(filepath) as f:
            data = json.load(f)

        features = []
        for feature in data.get("features", []):
            props = feature.get("properties", {})
            geom = feature.get("geometry", {})

            if geom.get("type") == "Point":
                coords = geom.get("coordinates", [0, 0])
                props["lon"] = coords[0]
                props["lat"] = coords[1]
            elif geom.get("type") in ["Polygon", "MultiPolygon"]:
                centroid = self._centroid(geom)
                props["lon"] = centroid[0]
                props["lat"] = centroid[1]

            features.append(props)

        self.sources_log.append({
            "file": filepath,
            "type": layer_type,
            "format": "geojson",
            "records": len(features),
            "timestamp": datetime.now().isoformat(),
        })

        return features

    def ingest_csv(self, filepath: str, lat_col: str = "lat", lon_col: str = "lon") -> list:
        """Ingest CSV with lat/long columns."""
        features = []
        with open(filepath) as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    row["lat"] = float(row.get(lat_col, 0))
                    row["lon"] = float(row.get(lon_col, 0))
                    features.append(row)
                except (ValueError, TypeError):
                    continue

        self.sources_log.append({
            "file": filepath,
            "type": "csv",
            "format": "csv",
            "records": len(features),
            "timestamp": datetime.now().isoformat(),
        })

        return features

    def normalize_to_features(self, raw_data: list, layer_type: str) -> list:
        """Normalize raw ingested data to internal feature schema."""
        normalized = []
        for record in raw_data:
            feat = {}
            for field in self.SCHEMA.get(layer_type, []):
                feat[field] = record.get(field, self._default_value(field))
            normalized.append(feat)
        return normalized

    def merge_layers(self, habitation_data: list, *layer_data) -> dict:
        """Merge multiple data layers into unified habitation features."""
        merged = {}
        for hab in habitation_data:
            key = hab.get("name", "").lower()
            merged[key] = {**hab}

        for layer in layer_data:
            for feat in layer:
                key = feat.get("name", "").lower()
                if key in merged:
                    merged[key].update(feat)

        return merged

    def get_sources_log(self) -> list:
        """Return data source audit trail."""
        return self.sources_log

    def _centroid(self, geometry: dict) -> list:
        """Compute rough centroid of geometry."""
        if geometry.get("type") == "Polygon":
            coords = geometry["coordinates"][0]
        elif geometry.get("type") == "MultiPolygon":
            coords = geometry["coordinates"][0][0]
        else:
            return [0, 0]

        lons = [c[0] for c in coords]
        lats = [c[1] for c in coords]
        return [sum(lons) / len(lons), sum(lats) / len(lats)]

    def _default_value(self, field: str):
        """Return sensible default for a field."""
        defaults = {
            "elevation": 100, "slope": 10, "rainfall_mm": 1500,
            "river_dist_km": 5, "flood_history": 0.3, "landslide_history": 0.2,
            "poverty_index": 0.3, "age_vulnerability": 0.25,
            "disability_index": 0.1, "infra_quality": 0.5,
            "road_dist_km": 5, "healthcare_dist_km": 10,
            "school_dist_km": 5, "water_availability": 0.6,
        }
        return defaults.get(field, 0)


pipeline = DataIngestionPipeline()
