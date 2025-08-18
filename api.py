import asyncio

from spider import BeikeMapSpider


async def main():
    with BeikeMapSpider() as spider:
        await spider.run()
        

if __name__ == '__main__':
    asyncio.run(main())