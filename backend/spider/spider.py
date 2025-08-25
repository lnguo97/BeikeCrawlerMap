import asyncio
import json
import typing
from datetime import datetime
from itertools import product

import httpx
import pandas as pd
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from .utils import init_logger, init_database, user_agent
from .models import (
    Cookie, 
    Community, CommunityProgress, 
    House, HouseProgress, 
)


class BeikeMapSpider:
    def __init__(self) -> None:
        self.ds = datetime.today().strftime(r'%Y%m%d')
        self.logger = init_logger(f'spider_{self.ds}')

        self.interrupted = False
        self.headers = None
        self.db_session = None
        
        self.MIN_LAT, self.MAX_LAT = 30.66, 31.89
        self.MIN_LON, self.MAX_LON = 120.86, 122.20

    def __enter__(self):
        # connect to database
        sessionmaker = init_database()
        self.db_session: Session = sessionmaker()

        # load cookie
        cookies = self.db_session.query(Cookie).all()
        if not cookies:
            raise ValueError('Cookie not found')
        cookies.sort(key=lambda c: c.crawl_time, reverse=True)
        self.headers = {
            'user-agent': user_agent,
            'cookie': cookies[0].text
        }
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db_session.commit()
        self.db_session.close()
        
    @staticmethod
    def get_community_list_url(
        min_lat: float,
        max_lat: float,
        min_lon: float,
        max_lon: float
    ) -> str:
        params = {
            'cityId': '310000',
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
            lat_range = float_range(self.MIN_LAT, self.MAX_LAT, step)
            lon_range = float_range(self.MIN_LON, self.MAX_LON, step)
            for lat, lon in product(lat_range, lon_range):
                self.db_session.add(
                    CommunityProgress(
                        ds=self.ds,
                        min_lat=lat, max_lat=round(lat + step, 2),
                        min_lon=lon, max_lon=round(lon + step, 2),
                    )
                )
            self.db_session.commit()

    async def crawl_community_list_data(
        self, 
        progress: CommunityProgress, 
        client: httpx.AsyncClient
    ):
        self.logger.info(
            f'Crawling community list, '
            f'latitute {progress.min_lat}-{progress.max_lat}, '
            f'longitude {progress.min_lon}-{progress.max_lon}'
        )
        res = await client.get(
            url=self.get_community_list_url(
                min_lat=progress.min_lat,
                max_lat=progress.max_lat,
                min_lon=progress.min_lon,
                max_lon=progress.max_lon,
            )
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
                bubble['group_type'] = progress.group_type
                self.db_session.add(Community(**bubble))
        progress.is_finished = True
        self.db_session.commit()

    async def crawl_community_list(self):
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
        max_concurrent = 3
        async with httpx.AsyncClient(headers=self.headers) as client:
            for i in range(0, len(progresses), max_concurrent):
                if self.interrupted:
                    return
                await asyncio.gather(*[
                    self.crawl_community_list_data(progress, client)
                    for progress in progresses[i:i + max_concurrent]
                ])
                await asyncio.sleep(0.1)

    async def crawl_community_detail_data(
        self, 
        community: Community,
        client: httpx.AsyncClient
    ):
        self.logger.info(f'Crawling details for community {community.id}')

        res = await client.get(f'https://sh.ke.com/xiaoqu/{community.id}/')
        soup = BeautifulSoup(res.content, 'html.parser')

        title = soup.select_one('.title')
        main_title = title.select_one('.main').get_text(strip=True)
        sub_title = title.select_one('.sub').get_text(strip=True)

        catalogs = soup.select_one('.intro.clear').find_all('a')
        block_name = catalogs[2].get_text(strip=True)

        follow_cnt = soup.find(id='favCount').get_text(strip=True)

        unit_price = soup.select_one('.xiaoquUnitPrice').get_text(strip=True)
        price_desc = soup.select_one('.xiaoquUnitPriceDesc').get_text(strip=True)

        info = {}
        info_items = soup.select('.xiaoquInfoItem')
        for item in info_items:
            label = item.select_one('.xiaoquInfoLabel').get_text(strip=True)
            content = item.select_one('.xiaoquInfoContent').get_text(strip=True)
            info[label] = content

        community.main_title = main_title
        community.sub_title = sub_title
        community.block_name = block_name
        community.follow_cnt = follow_cnt
        community.unit_price = unit_price
        community.price_desc = price_desc
        community.info = json.dumps(info, ensure_ascii=False)
        community.is_detail_crawled = True
        self.db_session.commit()

    async def crawl_community_detail(self):
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
        max_concurrent = 3
        headers = {'user-agent': user_agent}
        async with httpx.AsyncClient(headers=headers) as client:
            for i in range(0, len(communities), max_concurrent):
                if self.interrupted:
                    return
                await asyncio.gather(*[
                    self.crawl_community_detail_data(community, client)
                    for community in communities[i:i + max_concurrent]
                ])
                await asyncio.sleep(0.1)

    @staticmethod
    def get_house_list_url(community_id: int, page: int):
        params = {
            'cityId': 310000,
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

    async def crawl_house_list_data(
        self, 
        progress: HouseProgress, 
        client: httpx.AsyncClient
    ):
        self.logger.info(
            f'Crawling houses for community {progress.community_id}'
        )
        page = progress.finished_page + 1
        while progress.has_more:
            url = self.get_house_list_url(progress.community_id, page)
            res = await client.get(url)
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
                house['tags'] = '|'.join([tag['desc'] for tag in house['tags']])
                house['ds'] = self.ds
                house['community_id'] = progress.community_id
                self.db_session.add(House(**house))
            progress.finished_page = page
            progress.has_more = res.json()['data']['hasMore']
            self.db_session.commit()
            page += 1
        
    async def crawl_house_list(self):
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
        max_concurrent = 3
        async with httpx.AsyncClient(headers=self.headers) as client:
            for i in range(0, len(progresses), max_concurrent):
                if self.interrupted:
                    return
                await asyncio.gather(*[
                    self.crawl_house_list_data(progress, client)
                    for progress in progresses[i:i + max_concurrent]
                ])
                await asyncio.sleep(0.1)

    async def crawl_house_detail_data(
        self, 
        house: House,
        client: httpx.AsyncClient
    ):
        self.logger.info(f'Crawling details for house {house.id}')

        res = await client.get(house.actionUrl)
        soup = BeautifulSoup(res.content, 'html.parser')

        title = soup.select_one('.title')
        main_title = title.select_one('.main').get_text(strip=True)
        sub_title = title.select_one('.sub').get_text(strip=True)

        catalogs = soup.select_one('.intro.clear').find_all('a')
        district_name = catalogs[2].get_text(strip=True)
        block_name = catalogs[3].get_text(strip=True)
        
        follow_cnt = soup.find(id='favCount').get_text(strip=True)

        price = soup.select_one('.price-container')
        total_price = (
            price.select_one('.total').get_text(strip=True) + 
            price.select_one('.unit').get_text(strip=True)
        )
        unit_price = price.select_one('.unitPrice').get_text(strip=True)

        house_info = soup.select_one('.houseInfo')
        room_info = house_info.select_one('.room')
        room_main_info = room_info.select_one('.mainInfo').get_text(strip=True)
        room_sub_info = room_info.select_one('.subInfo').get_text(strip=True)

        type_info = house_info.select_one('.type')
        type_main_info = type_info.select_one('.mainInfo').get_text(strip=True)
        type_sub_info = type_info.select_one('.subInfo').get_text(strip=True)

        area_info = house_info.select_one('.area')
        area_main_info = area_info.select_one('.mainInfo').get_text(strip=True)
        area_sub_info = area_info.select_one('.subInfo').get_text(strip=True)

        house.main_title = main_title
        house.sub_title = sub_title
        house.district_name = district_name
        house.block_name = block_name
        house.follow_cnt = follow_cnt
        house.total_price = total_price
        house.unit_price = unit_price
        house.room_main_info = room_main_info
        house.room_sub_info = room_sub_info
        house.type_main_info = type_main_info
        house.type_sub_info = type_sub_info
        house.area_main_info = area_main_info
        house.area_sub_info = area_sub_info
        house.is_detail_crawled = True
        self.db_session.commit()

    async def crawl_house_detail(self):
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
        max_concurrent = 3
        headers = {'user-agent': user_agent}
        async with httpx.AsyncClient(headers=headers) as client:
            for i in range(0, len(houses), max_concurrent):
                if self.interrupted:
                    return
                await asyncio.gather(*[
                    self.crawl_house_detail_data(house, client)
                    for house in houses[i:i + max_concurrent]
                ])
                await asyncio.sleep(0.1)

    async def run(self):
        self.init_community_progress()
        await self.crawl_community_list()
        await self.crawl_community_detail()

        self.init_house_progress()
        await self.crawl_house_list()
        await self.crawl_house_detail()
