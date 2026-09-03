from sqlalchemy import Column, Integer, String, Float, JSON, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
from app.database import Base
import enum


class PriorityBand(str, enum.Enum):
    IMMEDIATE = "immediate"
    SHORT_TERM = "short_term"
    MEDIUM_TERM = "medium_term"
    MONITOR = "monitor"


class District(Base):
    __tablename__ = "districts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    state = Column(String, default="Assam")
    geom = Column(Geometry("MULTIPOLYGON", srid=4326))

    habitations = relationship("Habitation", back_populates="district")


class Habitation(Base):
    __tablename__ = "habitations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    district_id = Column(Integer, ForeignKey("districts.id"))
    population = Column(Integer)
    area_sq_km = Column(Float)
    geom = Column(Geometry("POINT", srid=4326))

    district = relationship("District", back_populates="habitations")
    hazard_scores = relationship("HazardScore", back_populates="habitation")
    risk_score = relationship("RiskScore", back_populates="habitation", uselist=False)
    relocation_sites = relationship("RelocationSite", back_populates="habitation")


class HazardScore(Base):
    __tablename__ = "hazard_scores"

    id = Column(Integer, primary_key=True, index=True)
    habitation_id = Column(Integer, ForeignKey("habitations.id"))
    flood_score = Column(Float)
    landslide_score = Column(Float)
    seismic_score = Column(Float)
    erosion_score = Column(Float)
    combined_hazard = Column(Float)
    confidence = Column(Float)
    model_version = Column(String)
    data_sources = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())

    habitation = relationship("Habitation", back_populates="hazard_scores")


class VulnerabilityScore(Base):
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
    created_at = Column(DateTime, server_default=func.now())


class RiskScore(Base):
    __tablename__ = "risk_scores"

    id = Column(Integer, primary_key=True, index=True)
    habitation_id = Column(Integer, ForeignKey("habitations.id"), unique=True)
    hazard_score = Column(Float)
    exposure_score = Column(Float)
    vulnerability_score = Column(Float)
    overall_risk = Column(Float)
    priority_band = Column(String)
    confidence = Column(Float)
    contributing_factors = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())

    habitation = relationship("Habitation", back_populates="risk_score")


class RelocationSite(Base):
    __tablename__ = "relocation_sites"

    id = Column(Integer, primary_key=True, index=True)
    habitation_id = Column(Integer, ForeignKey("habitations.id"))
    name = Column(String)
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
    carrying_capacity_verdict = Column(String)
    capacity_details = Column(JSON)
    geom = Column(Geometry("POINT", srid=4326))

    habitation = relationship("Habitation", back_populates="relocation_sites")


class Explanation(Base):
    __tablename__ = "explanations"

    id = Column(Integer, primary_key=True, index=True)
    habitation_id = Column(Integer, ForeignKey("habitations.id"))
    explanation_type = Column(String)
    text = Column(String)
    shap_values = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())
