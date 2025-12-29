from sqlalchemy import String, DateTime, Integer, Float, Text, func, Index
from sqlalchemy.orm import Mapped, mapped_column
from db import Base

class RouteConfig(Base):
    __tablename__ = "route_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    start_lat: Mapped[float] = mapped_column(Float, nullable=False)
    start_lng: Mapped[float] = mapped_column(Float, nullable=False)
    end_lat: Mapped[float] = mapped_column(Float, nullable=False)
    end_lng: Mapped[float] = mapped_column(Float, nullable=False)

    waze_region: Mapped[str] = mapped_column(String(8), nullable=False, default="IL")

    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Sample(Base):
    __tablename__ = "samples"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ts_utc: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    provider: Mapped[str] = mapped_column(String(16), nullable=False)  # "waze" | "osrm"
    status: Mapped[str] = mapped_column(String(16), nullable=False)    # "ok" | "error"

    duration_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    distance_m: Mapped[int | None] = mapped_column(Integer, nullable=True)

    error: Mapped[str | None] = mapped_column(String(512), nullable=True)
    raw_json: Mapped[str | None] = mapped_column(Text, nullable=True)

Index("ix_samples_provider_ts", Sample.provider, Sample.ts_utc)
