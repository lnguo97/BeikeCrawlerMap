import asyncio
import json
import logging
import os
import pathlib
import time
from datetime import datetime
from itertools import product

import requests
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker

from .models import (
    Base, City, Community, CommunityProgress, House, HouseProgress
)


class BeikeMapSpider:
    def __init__(self, city_name: str, Session: sessionmaker) -> None:
        self.ds = datetime.today().strftime(r'%Y%m%d')
        self.db_session = Session()
        self.city = (
            self.db_session.query(City)
            .filter(City.name == city_name)
            .first()
        )
        if not self.city:
            raise ValueError(f'Invalid city name: {city_name}')
        self.logger = None
        self.headers = None
        
    def __enter__(self):
        # initialize logger
        self.logger = logging.getLogger('spider')
        log_file = pathlib.Path(f'log/spider_{self.city_code}_{self.ds}.log')
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        self.logger.addHandler(file_handler)

        # initialize header
        self.headers = {
            'user-agent': (
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/138.0.0.0 '
                'Safari/537.36'
            )
        }
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # remove log file handler
        for handler in self.logger.handlers:
            if isinstance(handler, logging.FileHandler):
                self.logger.removeHandler(handler)
        
        # close database connection
        self.db_session.close()
        
    def get_community_list_url(
        self,
        min_lat: float,
        max_lat: float,
        min_lon: float,
        max_lon: float
    ) -> str:
        params = {
            'cityId': self.city_code,
            'dataSource': 'ESF',
            'groupType': 'community',
            'maxLatitude': max_lat,
            'minLatitude': min_lat,
            'maxLongitude': max_lon,
            'minLongitude': min_lon,
        }
        base_url = (
            'https://map.ke.com/proxyApi/i.c-pc-webapi.ke.com/map/bubblelist'
        )
        param_str = '&'.join([f'{k}={v}' for k, v in params.items()])
        return base_url + '?' + param_str
    
    def init_community_progress(self):
        def float_range(start, end, step, decimal=2):
            while start < end:
                yield round(start, decimal)
                start += step

        if not (
            self.db_session
            .query(CommunityProgress)
            .filter(CommunityProgress.ds == self.ds)
            .first()
        ):
            step = 0.05
            lat_range = float_range(self.min_lat, self.max_lat, step)
            lon_range = float_range(self.min_lon, self.max_lon, step)
            for lat, lon in product(lat_range, lon_range):
                self.db_session.add(
                    CommunityProgress(
                        ds=self.ds,
                        min_lat=lat, max_lat=round(lat + step, 2),
                        min_lon=lon, max_lon=round(lon + step, 2),
                    )
                )
            self.db_session.commit()

    def crawl_community_list(self):
        if self.interrupted:
            return
        progresses = (
            self.db_session
            .query(CommunityProgress)
            .filter(CommunityProgress.ds == self.ds)
            .filter(CommunityProgress.is_finished == 0)
            .all()
        )
        if not progresses:
            self.logger.info(f'All communities are crawled for date {self.ds}')
            return
        for progress in progresses:
            self.logger.info(
                f'Crawling community list, '
                f'latitute {progress.min_lat}-{progress.max_lat}, '
                f'longitude {progress.min_lon}-{progress.max_lon}'
            )
            res = requests.get(
                url=self.get_community_list_url(
                    min_lat=progress.min_lat,
                    max_lat=progress.max_lat,
                    min_lon=progress.min_lon,
                    max_lon=progress.max_lon,
                ),
                headers=self.headers
            )
            res.raise_for_status()
            data = res.json()['data']
            if 'bubbleList' in data:
                for bubble in data['bubbleList']:
                    if (
                        self.db_session.query(Community)
                        .filter(Community.id == bubble['id'])
                        .filter(Community.ds == self.ds)
                        .first()
                    ):
                        continue
                    bubble['ds'] = self.ds
                    self.db_session.add(Community(**bubble))
            progress.is_finished = True
            self.db_session.commit()
            if self.interrupted:
                return
            time.sleep(0.1)

    def crawl_community_detail(self):
        if self.interrupted:
            return
        communities = (
            self.db_session
            .query(Community)
            .filter(Community.ds == self.ds)
            .filter(Community.is_detail_crawled == 0)
            .all()
        )
        if not communities:
            self.logger.info(
                f'All community details are crawled for date {self.ds}'
            )
            return
        for community in communities:
            if self.interrupted:
                return
            self.logger.info(f'Crawling details for community {community.id}')
            res = requests.get(
                url=f'https://sh.ke.com/xiaoqu/{community.id}/',
                headers=self.headers
            )
            soup = BeautifulSoup(res.content, 'html.parser')
            
            # crawl title
            title = soup.select_one('.title')
            if title is not None:
                main_title = title.select_one('.main')
                if main_title is not None:
                    community.main_title = main_title.get_text(strip=True)
                sub_title = title.select_one('.sub')
                if sub_title is not None:
                    community.sub_title = sub_title.get_text(strip=True)

            # crawl catalog
            catalog = soup.select_one('.intro.clear')
            if catalog is not None: 
                catalogs = catalog.find_all('a')
                if len(catalogs) > 2:
                    community.block_name = catalogs[2].get_text(strip=True)

            # crawl follow count
            follow_cnt = soup.find(id='favCount')
            if follow_cnt is not None:
                community.follow_cnt = follow_cnt.get_text(strip=True)
            
            # crawl unit price
            unit_price = soup.select_one('.xiaoquUnitPrice')
            if unit_price is not None:
                community.unit_price = unit_price.get_text(strip=True)
            
            # crawl unit price
            price_desc = soup.select_one('.xiaoquUnitPriceDesc')
            if price_desc is not None:
                community.price_desc = price_desc.get_text(strip=True)

            # crawl other info
            info = {}
            info_items = soup.select('.xiaoquInfoItem')
            if info_items is not None:
                for item in info_items:
                    label = item.select_one('.xiaoquInfoLabel')
                    content = item.select_one('.xiaoquInfoContent')
                    if label is not None and content is not None:
                        label_text = label.get_text(strip=True)
                        content_text = content.get_text(strip=True)
                        info[label_text] = content_text
            if len(info) > 0:
                community.info = json.dumps(info, ensure_ascii=False)
                
            # save to database
            community.is_detail_crawled = True
            self.db_session.commit()
            time.sleep(0.1)

    def get_house_list_url(self, community_id: int, page: int):
        params = {
            'cityId': self.city_code,
            'dataSource': 'ESF',
            'curPage': page,
            'resblockId': community_id,
        }
        base_url = (
            'https://map.ke.com/proxyApi/i.c-pc-webapi.ke.com/map/houselist'
        )
        param_str = '&'.join([f'{k}={v}' for k, v in params.items()])
        return base_url + '?' + param_str

    def init_house_progress(self):
        if not (
            self.db_session
            .query(HouseProgress)
            .filter(HouseProgress.ds == self.ds)
            .first()
        ):
            communities = (
                self.db_session
                .query(Community.id)
                .filter(Community.ds == self.ds)
                .all()
            )
            for community in communities:
                progress = HouseProgress(ds=self.ds, community_id=community.id)
                self.db_session.add(progress)
            self.db_session.commit()
        
    def crawl_house_list(self):
        if self.interrupted:
            return
        progresses = (
            self.db_session
            .query(HouseProgress)
            .filter(HouseProgress.ds == self.ds)
            .filter(HouseProgress.has_more == 1)
            .all()
        )
        if not progresses:
            self.logger.info(f'All houses are crawled for date {self.ds}')
            return
        for progress in progresses:
            if self.interrupted:
                return
            self.logger.info(
                f'Crawling houses for community {progress.community_id}'
            )
            page = progress.finished_page + 1
            while progress.has_more:
                res = requests.get(
                    url=self.get_house_list_url(progress.community_id, page), 
                    headers=self.headers
                )
                house_list = res.json()['data']['list']
                for house in house_list:
                    house_id = house['actionUrl'].split('/')[-1].split('.')[0]
                    if (
                        self.db_session.query(House)
                        .filter(House.community_id == progress.community_id)
                        .filter(House.ds == self.ds)
                        .filter(House.id == house_id)
                        .first()
                    ):
                        continue
                    house['id'] = house_id
                    house['tags'] = '|'.join(
                        [tag['desc'] for tag in house['tags']]
                    )
                    house['ds'] = self.ds
                    house['community_id'] = progress.community_id
                    self.db_session.add(House(**house))
                progress.finished_page = page
                progress.has_more = res.json()['data']['hasMore']
                self.db_session.commit()
                page += 1
            time.sleep(0.1)

    def crawl_house_detail(self):
        if self.interrupted:
            return
        houses = (
            self.db_session
            .query(House)
            .filter(House.ds == self.ds)
            .filter(House.is_detail_crawled == 0)
            .all()
        )
        if not houses:
            self.logger.info(
                f'All house details are crawled for date {self.ds}'
            )
            return
        for house in houses:
            if self.interrupted:
                return
            self.logger.info(f'Crawling details for house {house.id}')
            res = requests.get(
                url=house.actionUrl, 
                headers=self.headers
            )
            soup = BeautifulSoup(res.content, 'html.parser')
            
            # crawl title
            title = soup.select_one('.title')
            if title is not None:
                main_title = title.select_one('.main')
                if main_title is not None:
                    house.main_title = main_title.get_text(strip=True)
                sub_title = title.select_one('.sub')
                if sub_title is not None:
                    house.sub_title = sub_title.get_text(strip=True)

            # crawl catalog
            catalog = soup.select_one('.intro.clear')
            if catalog is not None: 
                catalogs = catalog.find_all('a')
                if len(catalogs) > 2:
                    house.district_name = catalogs[2].get_text(strip=True)
                if len(catalogs) > 3:
                    house.block_name = catalogs[3].get_text(strip=True)

            # crawl follow count
            follow_cnt = soup.find(id='favCount')
            if follow_cnt is not None:
                house.follow_cnt = follow_cnt.get_text(strip=True)

            # crawl price
            price = soup.select_one('.price-container')
            if price is not None:
                total_price_num = price.select_one('.total')
                total_price_unit = price.select_one('.unit')
                unit_price = price.select_one('.unitPrice')
                if total_price_num is not None:
                    house.total_price_num = total_price_num.get_text(strip=True)
                if total_price_unit is not None:
                    house.total_price_unit = total_price_unit.get_text(strip=True)
                if unit_price is not None:
                    house.unit_price = unit_price.get_text(strip=True)
                    
            # crawl house info
            house_info = soup.select_one('.houseInfo')
            if house_info is not None:
                for info in ['room', 'type', 'area']:
                    info_tag = house_info.select_one(f'.{info}')
                    if info_tag is not None:
                        main_info = info_tag.select_one('.mainInfo')
                        sub_info = info_tag.select_one('.subInfo')
                        if main_info is not None:
                            setattr(
                                house, 
                                f'{info}_main_info', 
                                main_info.get_text(strip=True)
                            )
                        if sub_info is not None:
                            setattr(
                                house, 
                                f'{info}_sub_info', 
                                sub_info.get_text(strip=True)
                            )
            
            # submit to database
            house.is_detail_crawled = True
            self.db_session.commit()
            time.sleep(0.1)

    def run(self):
        self.init_community_progress()
        self.crawl_community_list()
        self.crawl_community_detail()

        self.init_house_progress()
        self.crawl_house_list()
        self.crawl_house_detail()
