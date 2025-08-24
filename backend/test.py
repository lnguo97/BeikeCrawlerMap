import asyncio

from spider import BeikeMapSpider


async def main():
    with BeikeMapSpider() as spider:
        await spider.run()


asyncio.run(main())