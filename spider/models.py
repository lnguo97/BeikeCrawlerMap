from sqlalchemy import String, Float, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase


class Base(DeclarativeBase):
    pass


class BubbleProgress(Base):
    __tablename__ = "bubble_progress"

    id: Mapped[int] = mapped_column(primary_key=True)
    ds: Mapped[str] = mapped_column(String(8))
    group_type: Mapped[str] = mapped_column(String(10))
    min_latitute: Mapped[float] = mapped_column(Float)
    max_latitute: Mapped[float] = mapped_column(Float)
    min_longitude: Mapped[float] = mapped_column(Float)
    max_longitude: Mapped[float] = mapped_column(Float)
    is_finished: Mapped[bool] = mapped_column(Boolean)


class HouseProgress(Base):
    __tablename__ = "bubble_progress"

    id: Mapped[int] = mapped_column(primary_key=True)
    ds: Mapped[str] = mapped_column(String(8))
    community_id: Mapped[str] = mapped_column(String(20))
    total_page: Mapped[int] = mapped_column(Integer, nullable=True)
    finished_page: Mapped[int] = mapped_column(Integer, default=0)
