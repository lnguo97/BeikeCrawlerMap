from datetime import datetime

from sqlalchemy import String, Text, Float, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase


class Base(DeclarativeBase):
    pass


class Cookie(Base):
    __tablename__ = 'cookies'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    crawl_time: Mapped[datetime] = mapped_column(DateTime)
    text: Mapped[str] = mapped_column(Text)


class LogRecord(Base):
    __tablename__ = 'log_records'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    level: Mapped[str] = mapped_column(String(20), nullable=False)
    logger_name: Mapped[str] = mapped_column(String(100), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    module: Mapped[str | None] = mapped_column(String(100))
    line_number: Mapped[int | None] = mapped_column(Integer)
    function_name: Mapped[str | None] = mapped_column(String(100))
    exception: Mapped[str | None] = mapped_column(Text)


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


class BubbleProgress(Base):
    __tablename__ = "bubble_progress"

    id: Mapped[int] = mapped_column(primary_key=True)
    ds: Mapped[str] = mapped_column(String(8))
    entity_type: Mapped[str] = mapped_column(String(10))
    min_latitute: Mapped[float] = mapped_column(Float)
    max_latitute: Mapped[float] = mapped_column(Float)
    min_longitude: Mapped[float] = mapped_column(Float)
    max_longitude: Mapped[float] = mapped_column(Float)
    is_finished: Mapped[bool] = mapped_column(Integer, default=0)


class House(Base):
    __tablename__ = "houses"
    
    index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    desc: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[str | None] = mapped_column(Text, nullable=True)
    coverPic: Mapped[str | None] = mapped_column(Text, nullable=True)
    priceStr: Mapped[str | None] = mapped_column(Text, nullable=True)
    unitPriceStr: Mapped[str | None] = mapped_column(Text, nullable=True)
    actionUrl: Mapped[str | None] = mapped_column(Text, nullable=True)
    cardType: Mapped[str | None] = mapped_column(Text, nullable=True)

    community_id: Mapped[int] = mapped_column(Integer)


class HouseProgress(Base):
    __tablename__ = "house_progress"

    id: Mapped[int] = mapped_column(primary_key=True)
    ds: Mapped[str] = mapped_column(String(8))
    community_id: Mapped[str] = mapped_column(String(20))
    total_page: Mapped[int] = mapped_column(Integer, default=-1)
    finished_page: Mapped[int] = mapped_column(Integer, default=-1)
