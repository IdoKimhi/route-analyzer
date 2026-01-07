from sqlalchemy import String, DateTime, Integer, Float, Text, func, Index, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db import Base

class Route(Base):
    __tablename__ = "routes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    name: Mapped[str] = mapped_column(String(64), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    start_lat: Mapped[float] = mapped_column(Float, nullable=False)
    start_lng: Mapped[float] = mapped_column(Float, nullable=False)
    end_lat: Mapped[float] = mapped_column(Float, nullable=False)
    end_lng: Mapped[float] = mapped_column(Float, nullable=False)

    waze_region: Mapped[str] = mapped_column(String(8), nullable=False, default="IL")

    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    samples: Mapped[list["Sample"]] = relationship(
        "Sample",
        back_populates="route",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

class Sample(Base):
    __tablename__ = "samples"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ts_utc: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    route_id: Mapped[int] = mapped_column(ForeignKey("routes.id", ondelete="CASCADE"), nullable=False, index=True)
    route: Mapped[Route] = relationship("Route", back_populates="samples")

    provider: Mapped[str] = mapped_column(String(16), nullable=False)  # "waze"
    status: Mapped[str] = mapped_column(String(16), nullable=False)    # "ok" | "error"

    duration_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    distance_m: Mapped[int | None] = mapped_column(Integer, nullable=True)

    error: Mapped[str | None] = mapped_column(String(512), nullable=True)
    raw_json: Mapped[str | None] = mapped_column(Text, nullable=True)

Index("ix_samples_route_provider_ts", Sample.route_id, Sample.provider, Sample.ts_utc)
