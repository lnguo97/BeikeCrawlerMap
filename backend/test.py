import asyncio

from spider import BeikeMapSpider


async def test_spider():
    with BeikeMapSpider() as spider:
        await spider.run()

asyncio.run(test_spider())
