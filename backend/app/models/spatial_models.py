"""PostGIS Spatial Models for SafeHabitat AI.

Production database schema with spatial indexing, audit trails,
and data source tracking.
"""
import os
from sqlalchemy import (
    Column, Integer, String, Float, JSON, DateTime, Boolean,
    ForeignKey, Text, Enum as SQLEnum, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum

IS_SQLITE = "sqlite" in os.getenv("DATABASE_URL", "sqlite:///./safehabitat.db")

if not IS_SQLITE:
    from geoalchemy2 import Geometry
else:
    Geometry = None  # type: ignore


class PriorityBand(str, enum.Enum):
    IMMEDIATE = "immediate"
    SHORT_TERM = "short_term"
    MEDIUM_TERM = "medium_term"
    MONITOR = "monitor"


class UserRole(str, enum.Enum):
    STATE_AUTHORITY = "state_authority"
    DISTRICT_OFFICER = "district_officer"
    VILLAGE_ANALYST = "village_analyst"
    ADMIN = "admin"


# --- Audit mixin ---
class AuditMixin:
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    data_source = Column(String(255))
    data_freshness = Column(DateTime)
    confidence = Column(Float)


# --- User & Auth ---
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default=UserRole.VILLAGE_ANALYST)
    district = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())


# --- Spatial Data Layers ---
class SpatialLayer(Base):
    __tablename__ = "spatial_layers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    layer_type = Column(String(100))  # dem, rainfall, river, road, etc.
    source = Column(String(255))
    source_url = Column(Text)
    format = Column(String(50))  # geojson, geotiff, shapefile
    crs = Column(String(50), default="EPSG:4326")
    resolution_meters = Column(Float)
    temporal_start = Column(DateTime)
    temporal_end = Column(DateTime)
    geom = Column(Geometry("MULTIPOLYGON", srid=4326)) if Geometry else Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON)
    last_updated = Column(DateTime, server_default=func.now())


class District(Base):
    __tablename__ = "districts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    state = Column(String(100), default="Assam")
    headquarters = Column(String(100))
    area_sq_km = Column(Float)
    population = Column(Integer)
    division = Column(String(100))
    geom = Column(Geometry("MULTIPOLYGON", srid=4326)) if Geometry else Column(Text, nullable=True)

    habitations = relationship("Habitation", back_populates="district")


class Habitation(Base, AuditMixin):
    __tablename__ = "habitations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    district_id = Column(Integer, ForeignKey("districts.id"))
    population = Column(Integer)
    area_sq_km = Column(Float)
    elevation_m = Column(Float)
    slope_degrees = Column(Float)
    geom = Column(Geometry("POINT", srid=4326)) if Geometry else Column(Text, nullable=True)

    district = relationship("District", back_populates="habitations")
    hazard_scores = relationship("HazardScore", back_populates="habitation", uselist=False)
    vulnerability_scores = relationship("VulnerabilityScore", back_populates="habitation", uselist=False)
    risk_score = relationship("RiskScore", back_populates="habitation", uselist=False)
    relocation_sites = relationship("RelocationSite", back_populates="habitation")
    explanations = relationship("Explanation", back_populates="habitation")

    __table_args__ = (
        Index("idx_habitation_district", "district_id"),
    ) if not IS_SQLITE else ()


class HazardScore(Base, AuditMixin):
    __tablename__ = "hazard_scores"

    id = Column(Integer, primary_key=True, index=True)
    habitation_id = Column(Integer, ForeignKey("habitations.id"), unique=True)
    flood_score = Column(Float)
    landslide_score = Column(Float)
    seismic_score = Column(Float)
    erosion_score = Column(Float)
    combined_hazard = Column(Float)
    model_version = Column(String(50))
    model_type = Column(String(50))  # xgboost, random_forest, deterministic

    # NRSC satellite data
    nrcs_very_high_villages = Column(Integer)
    nrcs_high_villages = Column(Integer)
    nrcs_moderate_villages = Column(Integer)
    nrcs_low_villages = Column(Integer)
    nrcs_very_low_villages = Column(Integer)
    nrcs_ranking = Column(String(10))
    nrcs_hazard_index = Column(Integer)
    nrcs_flood_waves = Column(Integer)
    nrcs_gauge_station = Column(String(255))

    habitation = relationship("Habitation", back_populates="hazard_scores")

    __table_args__ = (
        Index("idx_hazard_habitation", "habitation_id"),
    )


class VulnerabilityScore(Base, AuditMixin):
    __tablename__ = "vulnerability_scores"

    id = Column(Integer, primary_key=True, index=True)
    habitation_id = Column(Integer, ForeignKey("habitations.id"), unique=True)
    population_density = Column(Float)
    poverty_index = Column(Float)
    age_vulnerability = Column(Float)
    disability_index = Column(Float)
    infrastructure_quality = Column(Float)
    combined_vulnerability = Column(Float)
    weights = Column(JSON)

    habitation = relationship("Habitation", back_populates="vulnerability_scores")


class RiskScore(Base, AuditMixin):
    __tablename__ = "risk_scores"

    id = Column(Integer, primary_key=True, index=True)
    habitation_id = Column(Integer, ForeignKey("habitations.id"), unique=True)
    hazard_score = Column(Float)
    exposure_score = Column(Float)
    vulnerability_score = Column(Float)
    overall_risk = Column(Float)
    priority_band = Column(String(50))
    contributing_factors = Column(JSON)
    shap_values = Column(JSON)

    habitation = relationship("Habitation", back_populates="risk_score")


class RelocationSite(Base, AuditMixin):
    __tablename__ = "relocation_sites"

    id = Column(Integer, primary_key=True, index=True)
    habitation_id = Column(Integer, ForeignKey("habitations.id"))
    name = Column(String(255))
    area_sq_km = Column(Float)
    existing_population = Column(Integer)
    max_capacity = Column(Integer)
    water_availability = Column(Float)
    healthcare_access = Column(Float)
    school_access = Column(Float)
    road_access = Column(Float)
    environmental_suitability = Column(Float)
    livelihood_fit = Column(Float)
    suitability_score = Column(Float)
    carrying_capacity_verdict = Column(String(50))
    capacity_details = Column(JSON)
    geom = Column(Geometry("POINT", srid=4326)) if Geometry else Column(Text, nullable=True)

    habitation = relationship("Habitation", back_populates="relocation_sites")

    __table_args__ = ()


class Explanation(Base, AuditMixin):
    __tablename__ = "explanations"

    id = Column(Integer, primary_key=True, index=True)
    habitation_id = Column(Integer, ForeignKey("habitations.id"))
    explanation_type = Column(String(100))
    text = Column(Text)
    shap_values = Column(JSON)
    model_info = Column(JSON)

    habitation = relationship("Habitation", back_populates="explanations")


class DataIngestionLog(Base):
    __tablename__ = "data_ingestion_logs"

    id = Column(Integer, primary_key=True, index=True)
    source_name = Column(String(255))
    source_type = Column(String(100))
    source_url = Column(Text)
    records_ingested = Column(Integer)
    records_updated = Column(Integer)
    records_failed = Column(Integer)
    status = Column(String(50))  # success, partial, failed
    error_message = Column(Text)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_seconds = Column(Float)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(100))
    resource_type = Column(String(100))
    resource_id = Column(Integer)
    old_value = Column(JSON)
    new_value = Column(JSON)
    ip_address = Column(String(50))
    timestamp = Column(DateTime, server_default=func.now())
