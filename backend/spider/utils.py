import asyncio
import base64
import logging
import pathlib

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pydoll.browser.tab import Tab 

from .models import Base


USER_AGENT = (
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/138.0.0.0 '
    'Safari/537.36'
)


def init_database() -> sessionmaker:
    db_file_path = pathlib.Path('data/beike_house.db')
    db_file_path.parent.mkdir(exist_ok=True, parents=True)
    engine = create_engine(f'sqlite:///{db_file_path}')
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)


def init_logger(file_name: str):
    logger = logging.getLogger('spider')
    logger.setLevel(logging.DEBUG)
    log_file = pathlib.Path(f'log/{file_name}.log')
    log_file.parent.mkdir(exist_ok=True, parents=True)
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.info(f'logger initialized, output file: {log_file}')
    return logger


async def crawl_login_qr_code(tab: Tab) -> str:
    await tab.go_to('https://sh.ke.com/')
    login_btn = await tab.find(class_name="btn-login", timeout=5)
    await login_btn.click()
    qr_login_btn = await tab.query(
        '//*[@id="loginModel"]/div[2]/div[2]/div[4]/div[1]/ul/li[1]',
        timeout=5
    )
    await qr_login_btn.click()
    await asyncio.sleep(2)
    qr_img = await tab.find(class_name='qrcode_pic_container', timeout=5)
    img_path = pathlib.Path('temp/qr_code.png')
    img_path.parent.mkdir(parents=True, exist_ok=True)
    await qr_img.take_screenshot(img_path, quality=200)
    with open(img_path, 'rb') as image_file:
        base64_str = base64.b64encode(image_file.read()).decode('utf-8')
    return base64_str


async def crawl_login_status(tab: Tab) -> bool:
    login_info = await tab.find(class_name="typeShowUser", timeout=5)
    login_info_text = await login_info.text
    return login_info_text.endswith('退出')
