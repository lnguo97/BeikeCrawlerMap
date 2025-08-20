import asyncio
import json
import pathlib
import time

import streamlit as st
from streamlit.delta_generator import DeltaGenerator

from pydoll.browser.tab import Tab
from pydoll.browser import Chrome
from pydoll.protocol.network.types import CookieParam


cookie_path = pathlib.Path('data/cookies.json')


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


async def crawl_qr_code(tab: Tab, img_area: DeltaGenerator) -> None:
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
    pathlib.Path('temp/').mkdir(parents=True, exist_ok=True)
    await qr_img.take_screenshot('temp/qr_code.png', quality=200)
    with open('temp/qr_code.png', 'rb') as f:
        img_area.image(f.read())


async def check_is_login(tab: Tab, msg_area: DeltaGenerator) -> bool:
    is_login = False
    countdown_start = time.time()
    while not is_login and time.time() < countdown_start + 30:
        login_info = await tab.find(class_name="typeShowUser", timeout=5)
        login_info_text = await login_info.text
        if login_info_text.strip().endswith('退出'):
            with open(cookie_path, mode='w') as f:
                cookies = await tab.get_cookies()
                cookies = {
                    c['name']: c['value']
                    for c in cookies if c['domain'] == '.ke.com'
                }
                json.dump(cookies, f, indent=4)
            is_login = True
        time_left = int(30 - (time.time() - countdown_start))
        msg_area.text(f'Expire in {time_left} seconds')
        await asyncio.sleep(1)
    return is_login


async def main():
    st.title('Login Cookies')
    st.button('Login', icon=':material/login:', key='login_btn')
    if st.session_state.login_btn:
        async with Chrome() as browser:
            tab = await init_browser(browser, headless=True)
            img_area = st.empty()
            msg_area = st.empty()
            with st.spinner('Crawling QR code...'):
                await crawl_qr_code(tab, img_area)
            is_login = await check_is_login(tab, msg_area)
            if is_login:
                st.rerun()
            else:
                img_area.empty()
                msg_area.text('Login timeout, please try again')
    if cookie_path.exists():
        with open(cookie_path, mode='r') as f:
            cookies = json.load(f)
        st.json(cookies)


asyncio.run(main())
