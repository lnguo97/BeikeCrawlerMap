from datetime import datetime

from sqlalchemy import String, Text, Float, Integer, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase


class Base(DeclarativeBase):
    pass


# class Cookie(Base):
#     __tablename__ = 'cookies'

#     id: Mapped[int] = mapped_column(Integer, primary_key=True)
#     crawl_time: Mapped[datetime] = mapped_column(DateTime)
#     text: Mapped[str] = mapped_column(Text)


class City(Base):
    __tablename__ = "cities"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(8))
    url: Mapped[str] = mapped_column(String(256))
    code: Mapped[str] = mapped_column(String(8))
    min_lat: Mapped[float] = mapped_column(Float)
    max_lat: Mapped[float] = mapped_column(Float)
    min_lon: Mapped[float] = mapped_column(Float)
    max_lon: Mapped[float] = mapped_column(Float)


class Community(Base):
    __tablename__ = "communities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ds: Mapped[str] = mapped_column(String(8), primary_key=True)
    city_code: Mapped[str] = mapped_column(String(8), primary_key=True)
    
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
    name: Mapped[str | None] = mapped_column(Text, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    imageType: Mapped[int | None] = mapped_column(Integer, nullable=True)
    selected: Mapped[int | None] = mapped_column(Integer, nullable=True)

    is_detail_crawled: Mapped[bool] = mapped_column(Boolean, default=False)

    main_title: Mapped[str | None] = mapped_column(Text, nullable=True)
    sub_title: Mapped[str | None] = mapped_column(Text, nullable=True)
    block_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    follow_cnt: Mapped[str | None] = mapped_column(Text, nullable=True)
    unit_price: Mapped[str | None] = mapped_column(Text, nullable=True)
    price_desc: Mapped[str | None] = mapped_column(Text, nullable=True)
    info: Mapped[str | None] = mapped_column(Text, nullable=True)


class CommunityProgress(Base):
    __tablename__ = "community_progresses"

    id: Mapped[int] = mapped_column(primary_key=True)
    ds: Mapped[str] = mapped_column(String(8))
    city_code: Mapped[str] = mapped_column(String(8))

    min_lat: Mapped[float] = mapped_column(Float)
    max_lat: Mapped[float] = mapped_column(Float)
    min_lon: Mapped[float] = mapped_column(Float)
    max_lon: Mapped[float] = mapped_column(Float)
    is_finished: Mapped[bool] = mapped_column(Boolean, default=False)


class House(Base):
    __tablename__ = "houses"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    ds: Mapped[str] = mapped_column(String(8), primary_key=True)
    city_code: Mapped[str] = mapped_column(String(8), primary_key=True)
    community_id: Mapped[int] = mapped_column(Integer, primary_key=True)

    index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    desc: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[str | None] = mapped_column(Text, nullable=True)
    coverPic: Mapped[str | None] = mapped_column(Text, nullable=True)
    priceStr: Mapped[str | None] = mapped_column(Text, nullable=True)
    unitPriceStr: Mapped[str | None] = mapped_column(Text, nullable=True)
    actionUrl: Mapped[str | None] = mapped_column(Text, nullable=True)
    cardType: Mapped[str | None] = mapped_column(Text, nullable=True)

    is_detail_crawled: Mapped[bool] = mapped_column(Boolean, default=False)

    main_title: Mapped[str | None] = mapped_column(Text, nullable=True)
    sub_title: Mapped[str | None] = mapped_column(Text, nullable=True)
    district_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    block_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    follow_cnt: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_price_num: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_price_unit: Mapped[str | None] = mapped_column(Text, nullable=True)
    unit_price: Mapped[str | None] = mapped_column(Text, nullable=True)
    room_main_info: Mapped[str | None] = mapped_column(Text, nullable=True)
    room_sub_info: Mapped[str | None] = mapped_column(Text, nullable=True)
    type_main_info: Mapped[str | None] = mapped_column(Text, nullable=True)
    type_sub_info: Mapped[str | None] = mapped_column(Text, nullable=True)
    area_main_info: Mapped[str | None] = mapped_column(Text, nullable=True)
    area_sub_info: Mapped[str | None] = mapped_column(Text, nullable=True)


class HouseProgress(Base):
    __tablename__ = "house_progresses"

    id: Mapped[int] = mapped_column(primary_key=True)
    ds: Mapped[str] = mapped_column(String(8))
    city_code: Mapped[str] = mapped_column(String(8))
    
    community_id: Mapped[str] = mapped_column(String(20))
    finished_page: Mapped[int] = mapped_column(Integer, default=0)
    has_more: Mapped[bool] = mapped_column(Boolean, default=True)
