import asyncio
import json
import sqlite3
import typing

import pandas as pd

from pydoll.browser import Chrome
from pydoll.browser.tab import Tab
from pydoll.protocol.network.types import CookieParam


class BeikeMapSpider:
    def __init__(self) -> None:
        self.browser = Chrome()
        self.tab = None
        self.db_conn = sqlite3.connect('data/housing_data.db')
        self.MIN_LATITUTE, self.MAX_LATITUTE = 30.66, 31.89
        self.MIN_LONGITUDE, self.MAX_LONGITUDE = 120.86, 122.20

    async def init_browser(
        self,
        headless: bool = False, 
        cookies: list[dict] = None
    ):
        self.browser.options.headless = headless
        self.browser.options.add_argument(
            '--user-agent='
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/138.0.0.0 '
            'Safari/537.36'
        )
        self.tab = await self.browser.start()
        await self.browser.set_window_maximized()
        if cookies is not None:
            await self.tab.go_to('https://sh.ke.com/')
            await self.tab.set_cookies([
                CookieParam(**cookie) for cookie in cookies
            ])
            await self.tab.refresh()

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

    async def crawl_districts(self):
        self.db_conn.execute('drop table if exists districts;')
        url = self.get_bubble_list_url(
            group_type='district',
            min_latitude=self.MIN_LATITUTE,
            max_latitude=self.MAX_LATITUTE,
            min_longitude=self.MIN_LONGITUDE,
            max_longitude=self.MAX_LONGITUDE,
        )
        await self.tab.go_to(url)
        json_element = await self.tab.find(tag_name='pre', timeout=5)
        data = json.loads(await json_element.text)
        df = pd.DataFrame(data['data']['bubbleList'])
        df.to_sql('districts', self.db_conn, if_exists='append')
    
    async def crawl_bizcircles(self):
        self.db_conn.execute('drop table if exists bizcircles;')
        latitute = self.MIN_LATITUTE
        step = 0.2
        while latitute < self.MAX_LATITUTE:
            longitude = self.MIN_LONGITUDE
            while longitude < self.MAX_LONGITUDE:
                print(latitute, longitude)
                url = self.get_bubble_list_url(
                    group_type='bizcircle',
                    min_latitude=round(latitute, 2),
                    max_latitude=round(latitute + step, 2),
                    min_longitude=round(longitude, 2),
                    max_longitude=round(longitude + step, 2),
                )
                await self.tab.go_to(url)
                json_element = await self.tab.find(tag_name='pre', timeout=5)
                data = json.loads(await json_element.text)
                if data['data']['totalCount'] > 0:
                    df = pd.DataFrame(data['data']['bubbleList'])
                    df.to_sql('bizcircles', self.db_conn, if_exists='append')
                longitude += step
                await asyncio.sleep(2)
            latitute += step

    async def crawl_communities(
        self, 
        start_latitute: float | None = None, 
        drop_table = True,
        wait_interval: int = 2
    ):
        if drop_table:
            self.db_conn.execute('drop table if exists communities;')
        latitute = start_latitute or self.MIN_LATITUTE
        step = 0.05
        while latitute < self.MAX_LATITUTE:
            longitude = self.MIN_LONGITUDE
            while longitude < self.MAX_LONGITUDE:
                print(latitute, longitude)
                url = self.get_bubble_list_url(
                    group_type='community',
                    min_latitude=round(latitute, 2),
                    max_latitude=round(latitute + step, 2),
                    min_longitude=round(longitude, 2),
                    max_longitude=round(longitude + step, 2),
                )
                await self.tab.go_to(url)
                json_element = await self.tab.find(tag_name='pre', timeout=5)
                data = json.loads(await json_element.text)
                if data['data']['totalCount'] > 0:
                    df = pd.DataFrame(data['data']['bubbleList'])
                    df.to_sql('communities', self.db_conn, if_exists='append')
                longitude += step
                await asyncio.sleep(wait_interval)
            latitute += step

    async def run(self):
        with open('config/cookies.json') as f:
            cookies = json.load(f)
            cookies = [c for c in cookies if c['domain'] == '.ke.com']
        async with self.browser:
            await self.init_browser(headless=True, cookies=cookies)
            # await self.crawl_districts()
            # await self.crawl_bizcircles()
            await self.crawl_communities(drop_table=True, wait_interval=3)
            await asyncio.sleep(2)
        


async def main():
    spider = BeikeMapSpider()
    await spider.run()


if __name__ == '__main__':
    asyncio.run(main())
