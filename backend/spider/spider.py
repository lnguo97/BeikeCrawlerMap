import asyncio
import typing
from datetime import datetime
from itertools import product


import httpx
import pandas as pd
from sqlalchemy.orm import Session

from .utils import init_logger, init_database, user_agent
from .models import Cookie, Bubble, BubbleProgress, House, HouseProgress


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
    def get_bubble_list_url(
        group_type: typing.Literal['district', 'bizcircle', 'community'], 
        min_lat: float,
        max_lat: float,
        min_lon: float,
        max_lon: float
    ) -> str:
        params = {
            'cityId': '310000',
            'dataSource': 'ESF',
            'groupType': group_type,
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
    
    @staticmethod
    def float_range(start: float, end: float, step: float, decimal: int = 2):
        while start < end:
            yield round(start, decimal)
            start += step
    
    def init_bubble_progress(self):
        # init district bubble progress
        if not (
            self.db_session
            .query(BubbleProgress)
            .filter(BubbleProgress.group_type == 'district')
            .filter(BubbleProgress.ds == self.ds)
            .first()
        ):
            self.db_session.add(
                BubbleProgress(
                    ds=self.ds, group_type='district',
                    min_lat=self.MIN_LAT, max_lat=self.MAX_LAT,
                    min_lon=self.MIN_LON, max_lon=self.MAX_LON,
                )
            )
            self.db_session.commit()

        # init bizcircle bubble progress
        if not (
            self.db_session
            .query(BubbleProgress)
            .filter(BubbleProgress.group_type == 'bizcircle')
            .filter(BubbleProgress.ds == self.ds)
            .first()
        ):
            step = 0.2
            lat_range = self.float_range(self.MIN_LAT, self.MAX_LAT, step)
            lon_range = self.float_range(self.MIN_LON, self.MAX_LON, step)
            for lat, lon in product(lat_range, lon_range):
                self.db_session.add(
                    BubbleProgress(
                        ds=self.ds, group_type='bizcircle',
                        min_lat=lat, max_lat=round(lat + step, 2),
                        min_lon=lon, max_lon=round(lon + step, 2),
                    )
                )
                
            self.db_session.commit()

        # init community bubble progress
        if not (
            self.db_session
            .query(BubbleProgress)
            .filter(BubbleProgress.group_type == 'community')
            .filter(BubbleProgress.ds == self.ds)
            .first()
        ):
            step = 0.05
            lat_range = self.float_range(self.MIN_LAT, self.MAX_LAT, step)
            lon_range = self.float_range(self.MIN_LON, self.MAX_LON, step)
            for lat, lon in product(lat_range, lon_range):
                self.db_session.add(
                    BubbleProgress(
                        ds=self.ds, group_type='community',
                        min_lat=lat, max_lat=round(lat + step, 2),
                        min_lon=lon, max_lon=round(lon + step, 2),
                    )
                )
            self.db_session.commit()

    def init_house_progress(self):
        if not (
            self.db_session
            .query(HouseProgress)
            .filter(HouseProgress.ds == self.ds)
            .first()
        ):
            community_bubbles = (
                self.db_session
                .query(Bubble.id)
                .filter(Bubble.group_type == 'community')
                .filter(Bubble.ds == self.ds)
                .all()
            )
            for bubble in community_bubbles:
                progress = HouseProgress(ds=self.ds, community_id=bubble.id)
                self.db_session.add(progress)
            self.db_session.commit()

    async def crawl_bubble_data(
        self, 
        progress: BubbleProgress, 
        client: httpx.AsyncClient
    ):
        self.logger.info(
            f'Crawling {progress.group_type} bubble, '
            f'latitute {progress.min_lat}-{progress.max_lat}, '
            f'longitude {progress.min_lon}-{progress.max_lon}'
        )
        res = await client.get(
            url=self.get_bubble_list_url(
                group_type=progress.group_type,
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
                    self.db_session.query(Bubble)
                    .filter(Bubble.id == bubble['id'])
                    .filter(Bubble.ds == self.ds)
                    .filter(Bubble.group_type == progress.group_type)
                    .first()
                ):
                    continue
                bubble['ds'] = self.ds
                bubble['group_type'] = progress.group_type
                    
                self.db_session.add(Bubble(**bubble))
        progress.is_finished = True
        self.db_session.commit()

    async def crawl_bubbles(self):
        if self.interrupted:
            return
        progresses = (
            self.db_session
            .query(BubbleProgress)
            .filter(BubbleProgress.ds == self.ds)
            .filter(BubbleProgress.is_finished == 0)
            .all()
        )
        if not progresses:
            self.logger.info(f'All bubbles are crawled for date {self.ds}')
            return
        max_concurrent = 3
        async with httpx.AsyncClient(headers=self.headers) as client:
            for i in range(0, len(progresses), max_concurrent):
                if self.interrupted:
                    return
                await asyncio.gather(*[
                    self.crawl_bubble_data(progress, client)
                    for progress in progresses[i:i + max_concurrent]
                ])
                await asyncio.sleep(0.1)

    async def crawl_house_data(
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
                house_id = house['actionUrl'].split('/')[-2]
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
        
    async def crawl_houses(self):
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
                    self.crawl_house_data(progress, client)
                    for progress in progresses[i:i + max_concurrent]
                ])
                await asyncio.sleep(0.1)


    async def run(self):
        # self.init_bubble_progress()
        # await self.crawl_bubbles()
        self.init_house_progress()
        await self.crawl_houses()

