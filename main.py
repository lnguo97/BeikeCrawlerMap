import aiofiles
import asyncio
import json
import pathlib
import sqlite3
import time
import typing
from datetime import datetime

import pandas as pd

from pydoll.browser import Chrome
from pydoll.browser.tab import Tab
from pydoll.protocol.network.types import CookieParam


class BeikeMapSpider:
    def __init__(self, headless: bool = False) -> None:
        self.headless = headless
        self.cookies = None
        self.progress = None
        self.db_conn = None
        self.tab = None
        self.ds = datetime.today().strftime(r'%Y%m%d')
        self.MIN_LATITUTE, self.MAX_LATITUTE = 30.66, 31.89
        self.MIN_LONGITUDE, self.MAX_LONGITUDE = 120.86, 122.20

    def __enter__(self):
        # load cookies
        cookie_path = pathlib.Path('config/cookies.json')
        if cookie_path.exists():
            with open(cookie_path) as f:
                self.cookies = json.load(f)
                self.cookies = [
                    c for c in self.cookies 
                    if c['domain'] == '.ke.com'
                ]

        # load progress
        self.progress = {
            'district_finished': False,
            'bizcircle_latitute': self.MIN_LATITUTE,
            'community_latitute': self.MIN_LATITUTE,
        }
        progress_path = pathlib.Path('config/progress.json')
        if progress_path.exists():
            with open(progress_path) as f:
                progress = json.load(f)
            if self.ds in progress:
                self.progress = progress[self.ds]

        # connect to database
        self.db_conn = sqlite3.connect('data/housing_data.db')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # save cookies
        with open('config/cookies.json', mode='w') as f:
            json.dump(self.cookies, f, indent=2)

        # save progress
        progress_path = pathlib.Path('config/progress.json')
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

    async def login(self) -> bool:
        async with Chrome() as browser:
            await self.init_browser(browser)
            await self.tab.go_to('https://sh.ke.com/')
            login_btn = await self.tab.find(class_name="btn-login", timeout=5)
            await login_btn.click()
            qr_login_btn = await self.tab.query(
                '//*[@id="loginModel"]/div[2]/div[2]/div[4]/div[1]/ul/li[1]',
                timeout=5
            )
            await qr_login_btn.click()
            login_success = False
            start_time, timeout = time.time(), 30
            while not login_success and time.time() < start_time + timeout:
                print(f'Checking for login status: {login_success}')
                login_success = await self.check_is_login()
                if login_success:
                    self.cookies = await self.tab.get_cookies()
                await asyncio.sleep(2)
        return login_success

    async def check_is_login(self) -> bool:
        login_info = await self.tab.find(class_name="typeShowUser", timeout=5)
        return (await login_info.text).strip().endswith('退出')

    async def init_browser(self, browser: Chrome):
        browser.options.headless = self.headless
        browser.options.add_argument(
            '--user-agent='
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/138.0.0.0 '
            'Safari/537.36'
        )
        self.tab = await browser.start()
        await browser.set_window_maximized()
        if self.cookies is not None:
            await self.tab.go_to('https://sh.ke.com/')
            await self.tab.set_cookies([
                CookieParam(**cookie) for cookie in self.cookies
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
    
    def df_to_db(
        self, 
        df: pd.DataFrame, 
        table_name: str, 
        drop_table: bool
    ):
        if len(df) == 0:
            return
        if drop_table:
            self.db_conn.execute(f'drop table if exists {table_name};')
        df['ds'] = self.ds
        df.head(0).to_sql(table_name, self.db_conn, if_exists='append')
        id_list_str = ', '.join([f"'{i}'" for i in df['id']])
        self.db_conn.execute(
            f"delete from {table_name} "
            f"where id in ({id_list_str})"
            f"and ds = '{self.ds}';"
        )
        df.to_sql(table_name, self.db_conn, if_exists='append')

    async def crawl_districts(self, drop_table=False):
        if self.progress['district_finished']:
            print(f'District list is finished for date {self.ds}')
            return
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
        self.df_to_db(df, 'districts', drop_table)
        self.progress['district_finished'] = True
    
    async def crawl_bizcircles(self, drop_table=False):
        if self.progress['bizcircle_latitute'] >= self.MAX_LATITUTE:
            print(f'Bizcircle list is finished for date {self.ds}')
            return
        latitute = self.progress['bizcircle_latitute']
        step = 0.2
        while latitute < self.MAX_LATITUTE:
            longitude = self.MIN_LONGITUDE
            while longitude < self.MAX_LONGITUDE:
                print(
                    'Crawling bizcircle bubble list: '
                    f'({round(latitute, 2)}, {round(longitude, 2)})'
                )
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
                    self.df_to_db(df, 'bizcircles', drop_table)
                longitude += step
                await asyncio.sleep(2)
            latitute += step
            self.progress['bizcircle_latitute'] = round(latitute, 2)

    async def crawl_communities(
        self, 
        drop_table: bool = False,
        wait_interval: int = 2
    ):
        if self.progress['community_latitute'] >= self.MAX_LATITUTE:
            print(f'Community list is finished for date {self.ds}')
            return
        latitute = self.progress['community_latitute']
        step = 0.05
        while latitute < self.MAX_LATITUTE:
            longitude = self.MIN_LONGITUDE
            while longitude < self.MAX_LONGITUDE:
                print(
                    'Crawling community bubble list: '
                    f'({round(latitute, 2)}, {round(longitude, 2)})'
                )
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
                    self.df_to_db(df, 'communities', drop_table)
                longitude += step
                await asyncio.sleep(wait_interval)
            latitute += step
            self.progress['community_latitute'] = round(latitute, 2)

    async def run(self):
        async with Chrome() as browser:
            await self.init_browser(browser)
            if not await self.check_is_login():
                print('Credential expired, please login again...')
                login_success = await self.login()
                if not login_success:
                    print('Login timeout')
                    return
        async with Chrome() as browser:
            await self.init_browser(browser)
            await self.crawl_districts()
            await self.crawl_bizcircles()
            await self.crawl_communities()


async def main():
    with BeikeMapSpider(headless=False) as spider:
        await spider.run()
        

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Spider interrupted')
    except Exception as e:
        print(f'Other fatal error happened: {e}')
