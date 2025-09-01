import asyncio
import json
import logging
import os
import pathlib
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker

from spider import BeikeMapSpider
from spider.models import Base
from spider.models import City
from spider.models import Community, CommunityProgress
from spider.models import House, HouseProgress


@asynccontextmanager
async def lifespan(app: FastAPI):
    # initialize database
    db_url = os.getenv('DATABASE_URL') or 'sqlite:///data/beike_house.db'
    engine = create_engine(db_url)
    Base.metadata.create_all(bind=engine)
    app.state.Session = sessionmaker(bind=engine)
    
    # load city list
    with open('data/city_list.json') as f:
        city_list = json.load(f)
    with app.state.Session() as session:
        for city in city_list:
            if session.query(City).filter(City.name == city['name']).first():
                continue
            session.add(City(**city))
        session.commit()
    
    yield


app = FastAPI(lifespan=lifespan)


@app.get('/city_list')
async def get_city_list(request: Request):
    with request.app.state.Session() as session:
        city_list = session.query(City).all()
    return {
        city.name: city.code for city in city_list
    }


def start_spider(request: Request, city_code: str):
    try:
        with BeikeMapSpider(city_code, request.app.state.Session) as spider:
            request.app.state.spider = spider
            request.app.state.spider.run()
    finally:
        delattr(request.app.state, 'spider')


@app.post('/run_spider')
async def run_spider(
    city_code: str, request: Request, background_tasks: BackgroundTasks
):
    background_tasks.add_task(
        start_spider, request=request, city_code=city_code
    )
    return {'msg': 'spider started', 'city_code': city_code}


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
async def get_spider_progress(city_name: str, request: Request):
    with request.app.state.Session() as db_session:
        result = {}
        today_ds = datetime.today().strftime(r'%Y%m%d')
        result['ds'] = today_ds
        community_progresses = (
            db_session
            .query(CommunityProgress)
            .filter(CommunityProgress.ds == today_ds)
            .all()
        )
        result['community_list'] = {
            'finished': sum([p.is_finished for p in community_progresses]),
            'total': len(community_progresses)
        }
        house_progresses = (
            db_session
            .query(HouseProgress)
            .filter(HouseProgress.ds == today_ds)
            .all()
        )
        result['house_list'] = {
            'finished': sum([1 - p.has_more for p in house_progresses]),
            'total': len(house_progresses)
        }
        communities = (
            db_session
            .query(Community)
            .filter(Community.ds == today_ds)
            .all()
        )
        result['community_detail'] = {
            'finished': sum([c.is_detail_crawled for c in communities]),
            'total': len(communities)
        }
        houses = (
            db_session
            .query(House)
            .filter(House.ds == today_ds)
            .all()
        )
        result['house_detail'] = {
            'finished': sum([h.is_detail_crawled for h in houses]),
            'total': len(houses)
        }
    return result


@app.get('/spider_log')
async def get_spider_log():
    today_ds = datetime.today().strftime(r'%Y%m%d')
    spider_log = ''
    if pathlib.Path(f'log/spider_{today_ds}.log').exists():
        with open(f'log/spider_{today_ds}.log') as f:
            spider_log = f.read()
    return {'ds': today_ds, 'spider_log': spider_log}





# @app.get('/login_qr_code')
# async def get_login_qr_code(request: Request, headless: bool = True):
#     browser = Chrome()
#     browser.options.headless = headless
#     browser.options.add_argument(f'--user-agent={user_agent}')
#     tab = await browser.start()
#     await browser.set_window_maximized()
#     qr_code = await crawl_login_qr_code(tab)
#     request.app.state.browser = browser
#     request.app.state.tab = tab
#     return {'qr_code': qr_code}


# @app.get('/login_status')
# async def get_login_status(request: Request):
#     if not hasattr(request.app.state, 'tab'):
#         raise HTTPException(500, 'No active browser')
#     login_status = await crawl_login_status(request.app.state.tab)
#     return {'is_login': login_status}


# @app.post('/stop_browser')
# async def stop_browser(request: Request):
#     if hasattr(request.app.state, 'tab'):
#         await request.app.state.tab.close()
#     if hasattr(request.app.state, 'browser'):
#         await request.app.state.browser.stop()
#     return {'msg': 'browser stopped'}


# @app.post('/save_cookie')
# async def save_cookie(request: Request):
#     if not hasattr(request.app.state, 'tab'):
#         raise HTTPException(500, 'No active browser')
#     Session = init_database()
#     with Session() as session:
#         cookies = await request.app.state.tab.get_cookies()
#         cookie_text = '; '.join([
#             f"{cookie['name']}={cookie['value']}" for cookie in cookies
#         ])
#         session.add(Cookie(crawl_time=datetime.now(), text=cookie_text))
#         session.commit()
#     return {'msg': 'cookie saved to database'}


# @app.get('/cookie')
# async def get_cookie(request: Request):
#     Session = init_database()
#     with Session() as db_session:
#         cookies = db_session.query(Cookie).all()
#         if not cookies:
#             raise HTTPException(404, 'Cookie not found')
#         cookies.sort(key=lambda c: c.crawl_time, reverse=True)
#     return {
#         'crawl_time': cookies[0].crawl_time,
#         'text': cookies[0].text,
#     }


