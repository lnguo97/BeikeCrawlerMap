import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, BackgroundTasks

from spider import BeikeMapSpider


app = FastAPI()


@app.post('/run_spider')
async def run_spider(request: Request, background_tasks: BackgroundTasks):
    def start_spider():
        with BeikeMapSpider() as spider:
            request.app.state.spider = spider
            asyncio.run(spider.run())
            delattr(request.app.state, 'spider')

    background_tasks.add_task(start_spider)


@app.post('/stop_spider')
async def run_spider(request: Request):
    request.app.state.spider.interrupted = True


@app.get('/is_spider_running')
async def run_spider(request: Request):
    return hasattr(request.app, 'spider')
