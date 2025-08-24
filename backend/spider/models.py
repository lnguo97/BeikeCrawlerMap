from datetime import datetime

from sqlalchemy import String, Text, Float, Integer, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase


class Base(DeclarativeBase):
    pass


class Cookie(Base):
    __tablename__ = 'cookies'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    crawl_time: Mapped[datetime] = mapped_column(DateTime)
    text: Mapped[str] = mapped_column(Text)


class Bubble(Base):
    __tablename__ = "bubbles"
    
    index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fullSpell: Mapped[str | None] = mapped_column(Text, nullable=True)
    desc: Mapped[str | None] = mapped_column(Text, nullable=True)
    count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    countStr: Mapped[str | None] = mapped_column(Text, nullable=True)
    countUnit: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[str | None] = mapped_column(Text, nullable=True)
    priceStr: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str | None] = mapped_column(Text, nullable=True)
    priceUnit: Mapped[str | None] = mapped_column(Text, nullable=True)
    border: Mapped[str | None] = mapped_column(Text, nullable=True)
    bubbleDesc: Mapped[str | None] = mapped_column(Text, nullable=True)
    icon: Mapped[str | None] = mapped_column(Text, nullable=True)
    entityId: Mapped[str | None] = mapped_column(Text, nullable=True)
    entityType: Mapped[str | None] = mapped_column(Text, nullable=True)
    hideHouseCount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str | None] = mapped_column(Text, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    imageType: Mapped[int | None] = mapped_column(Integer, nullable=True)
    selected: Mapped[int | None] = mapped_column(Integer, nullable=True)

    ds: Mapped[str] = mapped_column(String(8), primary_key=True)
    group_type: Mapped[str] = mapped_column(String(10), primary_key=True)


class BubbleProgress(Base):
    __tablename__ = "bubble_progress"

    id: Mapped[int] = mapped_column(primary_key=True)
    ds: Mapped[str] = mapped_column(String(8))
    group_type: Mapped[str] = mapped_column(String(10))
    min_lat: Mapped[float] = mapped_column(Float)
    max_lat: Mapped[float] = mapped_column(Float)
    min_lon: Mapped[float] = mapped_column(Float)
    max_lon: Mapped[float] = mapped_column(Float)
    is_finished: Mapped[bool] = mapped_column(Boolean, default=False)


class House(Base):
    __tablename__ = "houses"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    desc: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[str | None] = mapped_column(Text, nullable=True)
    coverPic: Mapped[str | None] = mapped_column(Text, nullable=True)
    priceStr: Mapped[str | None] = mapped_column(Text, nullable=True)
    unitPriceStr: Mapped[str | None] = mapped_column(Text, nullable=True)
    actionUrl: Mapped[str | None] = mapped_column(Text, nullable=True)
    cardType: Mapped[str | None] = mapped_column(Text, nullable=True)

    ds: Mapped[str] = mapped_column(String(8), primary_key=True)
    community_id: Mapped[int] = mapped_column(Integer, primary_key=True)


class HouseProgress(Base):
    __tablename__ = "house_progress"

    id: Mapped[int] = mapped_column(primary_key=True)
    ds: Mapped[str] = mapped_column(String(8))
    community_id: Mapped[str] = mapped_column(String(20))
    finished_page: Mapped[int] = mapped_column(Integer, default=0)
    has_more: Mapped[bool] = mapped_column(Boolean, default=True)
