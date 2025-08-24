import asyncio
import pathlib
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from pydoll.browser import Chrome

from spider import BeikeMapSpider
from spider.models import Cookie, BubbleProgress
from spider.utils import (
    crawl_login_qr_code, crawl_login_status, init_database, user_agent
)


app = FastAPI()


@app.get('/login_qr_code')
async def get_login_qr_code(request: Request, headless: bool = True):
    browser = Chrome()
    browser.options.headless = headless
    browser.options.add_argument(f'--user-agent={user_agent}')
    tab = await browser.start()
    await browser.set_window_maximized()
    qr_code = await crawl_login_qr_code(tab)
    request.app.state.browser = browser
    request.app.state.tab = tab
    return {'qr_code': qr_code}


@app.get('/login_status')
async def get_login_status(request: Request):
    if not hasattr(request.app.state, 'tab'):
        raise HTTPException(500, 'No active browser')
    login_status = await crawl_login_status(request.app.state.tab)
    return {'is_login': login_status}


@app.post('/stop_browser')
async def stop_browser(request: Request):
    if hasattr(request.app.state, 'tab'):
        await request.app.state.tab.close()
    if hasattr(request.app.state, 'browser'):
        await request.app.state.browser.stop()
    return {'msg': 'browser stopped'}


@app.post('/save_cookie')
async def save_cookie(request: Request):
    if not hasattr(request.app.state, 'tab'):
        raise HTTPException(500, 'No active browser')
    Session = init_database()
    with Session() as session:
        cookies = await request.app.state.tab.get_cookies()
        cookie_text = '; '.join([
            f"{cookie['name']}={cookie['value']}" for cookie in cookies
        ])
        session.add(Cookie(crawl_time=datetime.now(), text=cookie_text))
        session.commit()
    return {'msg': 'cookie saved to database'}


@app.get('/cookie')
async def get_cookie(request: Request):
    Session = init_database()
    with Session() as db_session:
        cookies = db_session.query(Cookie).all()
        if not cookies:
            raise HTTPException(404, 'Cookie not found')
        cookies.sort(key=lambda c: c.crawl_time, reverse=True)
    return {
        'crawl_time': cookies[0].crawl_time,
        'text': cookies[0].text,
    }


@app.post('/run_spider')
async def run_spider(request: Request, background_tasks: BackgroundTasks):
    async def start_spider():
        try:
            with BeikeMapSpider() as spider:
                request.app.state.spider = spider
                await spider.run()
        finally:
            if hasattr(request.app.state, 'spider'):
                delattr(request.app.state, 'spider')

    background_tasks.add_task(lambda: asyncio.run(start_spider()))
    return {'msg': 'spider started'}


@app.get('/is_spider_running')
async def get_is_spider_running(request: Request):
    return {'is_spider_running': hasattr(request.app.state, 'spider')}


@app.post('/stop_spider')
async def stop_spider(request: Request):
    if not hasattr(request.app.state, 'spider'):
        raise HTTPException(404, 'No running spider')
    request.app.state.spider.interrupted = True
    return {'msg': 'spider stopped'}


@app.get('/spider_progress')
async def get_spider_progress():
    Session = init_database()
    with Session() as db_session:
        result = {}
        today_ds = datetime.today().strftime(r'%Y%m%d')
        for group_type in ['district', 'bizcircle', 'community']:
            progresses = (
                db_session
                .query(BubbleProgress)
                .filter(BubbleProgress.ds == today_ds)
                .filter(BubbleProgress.group_type == group_type)
                .all()
            )
            result[group_type] = {
                'finished': sum([p.is_finished for p in progresses]),
                'total': len(progresses)
            }
    return result


@app.get('/spider_log')
async def get_spider_log(limit: int = 200):
    today_ds = datetime.today().strftime(r'%Y%m%d')
    if not pathlib.Path(f'log/spider_{today_ds}.log').exists():
        raise HTTPException(500, 'Spider log not found')
    with open(f'log/spider_{today_ds}.log') as f:
        lines = f.readlines()
        lines.reverse()
    return {
        'spider_log': ''.join(lines[:limit])
    }
