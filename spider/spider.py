import aiofiles
import asyncio
import json
import pathlib
import sqlite3
import time
import typing
from datetime import datetime

import httpx
import pandas as pd

from pydoll.browser import Chrome
from pydoll.browser.tab import Tab
from pydoll.protocol.network.types import CookieParam


class BeikeMapSpider:
    def __init__(self) -> None:
        self.cookies = None
        self.progress = None
        self.db_conn = None
        self.ds = datetime.today().strftime(r'%Y%m%d')
        self.MIN_LATITUTE, self.MAX_LATITUTE = 30.66, 31.89
        self.MIN_LONGITUDE, self.MAX_LONGITUDE = 120.86, 122.20

    def __enter__(self):
        # load cookies
        cookie_path = pathlib.Path('data/cookies.json')
        if cookie_path.exists():
            with open(cookie_path) as f:
                self.cookies = json.load(f)

        # load progress
        self.progress = {
            'district_finished': False,
            'bizcircle_latitute': self.MIN_LATITUTE,
            'community_latitute': self.MIN_LATITUTE,
            'house_community': -1
        }
        progress_path = pathlib.Path('data/progress.json')
        if progress_path.exists():
            with open(progress_path) as f:
                progress = json.load(f)
            if self.ds in progress:
                self.progress = progress[self.ds]

        # connect to database
        self.db_conn = sqlite3.connect('data/housing_data.db')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # save progress
        progress_path = pathlib.Path('data/progress.json')
        if not progress_path.exists():
            all_progress = {self.ds: self.progress}
        else:
            with open(progress_path) as f:
                all_progress = json.load(f)
                all_progress[self.ds] = self.progress
        with open(progress_path, mode='w') as f:
            json.dump(all_progress, f, indent=2)

        # close database connection
        self.db_conn.close()
        return False

    @property
    def headers(self):
        return {
            'user-agent': (
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/138.0.0.0 '
                'Safari/537.36'
            ),
            'cookie': '; '.join([f'{k}={v}' for k, v in self.cookies.items()])
        }
        
    @staticmethod
    def get_bubble_list_url(
        group_type: typing.Literal['district', 'bizcircle', 'community'], 
        min_latitude: float,
        max_latitude: float,
        min_longitude: float,
        max_longitude: float
    ) -> str:
        params = {
            'cityId': '310000',
            'dataSource': 'ESF',
            'groupType': group_type,
            'maxLatitude': max_latitude,
            'minLatitude': min_latitude,
            'maxLongitude': max_longitude,
            'minLongitude': min_longitude,
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
    def chunk_area(
        min_latitute: float, 
        max_latitute: float, 
        min_longitude: float,
        max_longitude: float,
        step: float
    ):
        lat = min_latitute
        while lat < max_latitute:
            lon = min_longitude
            while lon < max_longitude:
                yield lat, lon
                lon += step
            lat += step

    def df_to_db(
        self, 
        df: pd.DataFrame, 
        table_name: str, 
        pk_column: str = 'id'
    ):
        if len(df) == 0:
            return
        df['ds'] = self.ds
        df.head(0).to_sql(table_name, self.db_conn, if_exists='append')
        pk_list_str = ', '.join([f"'{i}'" for i in df[pk_column]])
        self.db_conn.execute(
            f"delete from {table_name} "
            f"where {pk_column} in ({pk_list_str})"
            f"and ds = '{self.ds}';"
        )
        df.to_sql(table_name, self.db_conn, if_exists='append')

    async def crawl_districts(self):
        if self.progress['district_finished']:
            print(f'District list is finished for date {self.ds}')
            return
        print('Crawling district bubble list')
        url = self.get_bubble_list_url(
            group_type='district',
            min_latitude=self.MIN_LATITUTE,
            max_latitude=self.MAX_LATITUTE,
            min_longitude=self.MIN_LONGITUDE,
            max_longitude=self.MAX_LONGITUDE,
        )
        res = httpx.get(url, headers=self.headers)
        df = pd.DataFrame(res.json()['data']['bubbleList'])
        self.df_to_db(df, 'districts')
        print(df.head())
        self.progress['district_finished'] = True
    
    async def crawl_bizcircles(self):
        if self.progress['bizcircle_latitute'] >= self.MAX_LATITUTE:
            print(f'Bizcircle list is finished for date {self.ds}')
            return
        step = 0.2
        async with httpx.AsyncClient(headers=self.headers) as client:
            for lat, lon in self.chunk_area(
                min_latitute=self.progress['bizcircle_latitute'],
                max_latitute=self.MAX_LATITUTE,
                min_longitude=self.MIN_LONGITUDE,
                max_longitude=self.MAX_LONGITUDE,
                step=step
            ):
                print(f'Crawling bizcircle bubble list: '
                      f'({round(lat, 2)}, {round(lon, 2)})')
                url = self.get_bubble_list_url(
                    group_type='bizcircle',
                    min_latitude=round(lat, 2),
                    max_latitude=round(lat + step, 2),
                    min_longitude=round(lon, 2),
                    max_longitude=round(lon + step, 2),
                )
                res = await client.get(url)
                if res.json()['data']['totalCount'] > 0:
                    df = pd.DataFrame(res.json()['data']['bubbleList'])
                    self.df_to_db(df, 'bizcircles')
                    print(df.head())
                # await asyncio.sleep(1)
                self.progress['bizcircle_latitute'] = round(lat, 2)

    async def crawl_communities(self):
        if self.progress['community_latitute'] >= self.MAX_LATITUTE:
            print(f'Community list is finished for date {self.ds}')
            return
        step = 0.05
        async with httpx.AsyncClient(headers=self.headers) as client:
            for lat, lon in self.chunk_area(
                min_latitute=self.progress['community_latitute'],
                max_latitute=self.MAX_LATITUTE,
                min_longitude=self.MIN_LONGITUDE,
                max_longitude=self.MAX_LONGITUDE,
                step=step
            ):
                print(f'Crawling community bubble list: '
                      f'({round(lat, 2)}, {round(lon, 2)})')
                url = self.get_bubble_list_url(
                    group_type='community',
                    min_latitude=round(lat, 2),
                    max_latitude=round(lat + step, 2),
                    min_longitude=round(lon, 2),
                    max_longitude=round(lon + step, 2),
                )
                res = await client.get(url)
                if res.json()['data']['totalCount'] > 0:
                    df = pd.DataFrame(res.json()['data']['bubbleList'])
                    self.df_to_db(df, 'communities')
                    print(df.head())
                # await asyncio.sleep(1)
            self.progress['community_latitute'] = round(lat, 2)
            
    async def crawl_houses(self):
        all_communities = self.db_conn.execute(
            f"select distinct id from communities where ds = '{self.ds}'"
        ).fetchall()
        target_communities = [
            record[0]
            for record in all_communities
            if record[0] >= self.progress['house_community']
        ]
        if not target_communities:
            print(f'House list is finished for date {self.ds}')
        target_communities.sort()
        async with httpx.AsyncClient(headers=self.headers) as client:
            for community_id in target_communities:
                page = 1
                while True:
                    print(f'Crawling house list for community '
                          f'{community_id} page {page}')
                    url = self.get_house_list_url(community_id, page)
                    res = await client.get(url)
                    house_list = res.json()['data']['list']
                    for house in house_list:
                        house['tags'] = '|'.join([
                            tag['desc'] for tag in house['tags']
                        ])
                    df = pd.DataFrame(house_list)
                    self.df_to_db(df, 'houses', pk_column='actionUrl')
                    if res.json()['data']['hasMore'] == 0:
                        break
                    page += 1
                    # await asyncio.sleep(1)
                self.progress['house_community'] = community_id

    async def run(self):
        await self.crawl_districts()
        await self.crawl_bizcircles()
        await self.crawl_communities()
        await self.crawl_houses()
