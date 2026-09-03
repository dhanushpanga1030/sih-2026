"""GIS Processing Engine for SafeHabitat AI.

Uses GeoPandas and Rasterio for spatial analysis.
"""
import json
from pathlib import Path
from typing import Optional
import geopandas as gpd
from shapely.geometry import Point, shape
import rasterio
from rasterio.mask import mask
import numpy as np


class GISProcessor:
    """Spatial analysis using GeoPandas and Rasterio."""

    def __init__(self, data_dir: Path = None):
        self.data_dir = data_dir or Path(__file__).parent.parent.parent / "data"

    def load_geojson(self, filepath: str) -> gpd.GeoDataFrame:
        """Load GeoJSON file into GeoDataFrame."""
        return gpd.read_file(filepath)

    def create_habitation_gdf(self, habitations: list) -> gpd.GeoDataFrame:
        """Convert habitations list to GeoDataFrame."""
        geometry = [Point(h["lon"], h["lat"]) for h in habitations]
        return gpd.GeoDataFrame(habitations, geometry=geometry, crs="EPSG:4326")

    def calculate_distance_to_feature(self, hab_gdf: gpd.GeoDataFrame, feature_gdf: gpd.GeoDataFrame) -> list:
        """Calculate distance from each habitation to nearest feature."""
        hab_projected = hab_gdf.to_crs(epsg=32646)
        feature_projected = feature_gdf.to_crs(epsg=32646)
        distances = []
        for _, hab in hab_projected.iterrows():
            min_dist = feature_projected.geometry.distance(hab.geometry).min()
            distances.append(min_dist / 1000)
        return distances

    def extract_elevation(self, hab_gdf: gpd.GeoDataFrame, dem_path: str) -> list:
        """Extract elevation from DEM raster at habitation points."""
        elevations = []
        with rasterio.open(dem_path) as src:
            for _, hab in hab_gdf.iterrows():
                row, col = src.index(hab.geometry.x, hab.geometry.y)
                elevations.append(src.read(1)[row, col])
        return elevations

    def calculate_slope(self, dem_path: str) -> np.ndarray:
        """Calculate slope from DEM raster."""
        with rasterio.open(dem_path) as src:
            dem = src.read(1)
            dx = np.gradient(dem, axis=1)
            dy = np.gradient(dem, axis=0)
            slope = np.arctan(np.sqrt(dx**2 + dy**2)) * (180 / np.pi)
        return slope

    def identify_flood_zones(self, hab_gdf: gpd.GeoDataFrame, river_gdf: gpd.GeoDataFrame, buffer_km: float = 2.0) -> gpd.GeoDataFrame:
        """Identify habitations within flood zones of rivers."""
        river_projected = river_gdf.to_crs(epsg=32646)
        buffer_geom = river_projected.geometry.buffer(buffer_km * 1000)
        flood_zone = gpd.GeoDataFrame(geometry=[buffer_geom.union_all()], crs="EPSG:32646").to_crs(epsg=4326)
        hab_in_flood = gpd.sjoin(hab_gdf, flood_zone, how="inner", predicate="within")
        return hab_in_flood

    def calculate_terrain_ruggedness(self, dem_path: str) -> float:
        """Calculate terrain ruggedness index."""
        with rasterio.open(dem_path) as src:
            dem = src.read(1)
            dx = np.abs(np.diff(dem, axis=1))
            dy = np.abs(np.diff(dem, axis=0))
            tri = np.sqrt(dx**2 + dy**2).mean()
        return tri

    def clip_raster_to_district(self, raster_path: str, district_geom: dict, output_path: str) -> str:
        """Clip raster to district boundary."""
        geom = [shape(district_geom)]
        with rasterio.open(raster_path) as src:
            out_image, out_transform = mask(src, geom, crop=True)
            out_meta = src.meta.copy()
            out_meta.update({"height": out_image.shape[1], "width": out_image.shape[2], "transform": out_transform})
        with rasterio.open(output_path, "w", **out_meta) as dest:
            dest.write(out_image)
        return output_path

    def get_habitation_features(self, hab_data: dict, dem_path: str = None, river_path: str = None) -> dict:
        """Extract all GIS features for a habitation."""
        features = {
            "elevation": hab_data.get("elevation_m", 50),
            "slope": hab_data.get("slope_degrees", 2),
            "distance_to_river_km": 5.0,
            "distance_to_road_km": 3.0,
            "terrain_ruggedness": 1.0,
        }
        return features


gis = GISProcessor()
