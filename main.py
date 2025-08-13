import asyncio
import json

from pydoll.browser import Chrome
from pydoll.browser.tab import Tab
from pydoll.protocol.network.types import CookieParam


async def init_browser(
    browser: Chrome, 
    headless: bool = True, 
    cookies: list[dict] = None
) -> Tab:
    browser.options.headless = headless
    browser.options.add_argument(
        '--user-agent='
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/138.0.0.0 '
        'Safari/537.36'
    )
    tab = await browser.start()
    await browser.set_window_maximized()
    if cookies is not None:
        await tab.go_to('https://sh.ke.com/')
        await tab.set_cookies([
            CookieParam(**cookie) for cookie in cookies
        ])
        await tab.refresh()
    return tab


def degree_to_decimal(degrees: int, minutes: int) -> float:
    return degrees + minutes/60


async def main():
    with open('config/cookies.json') as f:
        cookies = json.load(f)
        cookies = [c for c in cookies if c['domain'] == '.ke.com']
    async with Chrome() as browser:
        tab = await init_browser(browser, headless=False, cookies=cookies)
        latitude, end_latitude = 120.86, 122.20
        longitude, end_longitude = 30.66, 31.89
        
        file_cnt = 1
        step = 0.5
        while latitude < end_latitude:
            while longitude < end_longitude:
                url = (
                    'https://map.ke.com/proxyApi/i.c-pc-webapi.ke.com/map/bubblelist?'
                    'cityId=310000&dataSource=ESF&groupType=community&'
                    f'maxLatitude={round(latitude + step, 14)}&'
                    f'minLatitude={round(latitude, 14)}&'
                    f'maxLongitude={round(longitude + step, 14)}&'
                    f'minLongitude={round(longitude, 14)}'
                )
                print(url)
                await tab.go_to(url)
                json_element = await tab.find(tag_name='pre', timeout=5)
                data = json.loads(await json_element.text)
                if data['data']['totalCount'] > 0:
                    with open(f'data/community{file_cnt}.json', mode='w') as f:
                        json.dump(data, f, indent=4, ensure_ascii=False)
                    file_cnt += 1
                await asyncio.sleep(10)
                longitude += step
            latitude += step
                

        input()


if __name__ == '__main__':
    asyncio.run(main())
