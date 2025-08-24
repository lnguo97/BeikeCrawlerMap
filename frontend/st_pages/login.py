import asyncio
import base64
import json
import os
import pathlib
import time

import httpx
import streamlit as st


def main():
    base_url = os.getenv('BACKEND_URL') or 'http://localhost:8000'

    st.title('Login Cookies')
    with st.container(
        horizontal=True, 
        horizontal_alignment="left", 
        vertical_alignment='center'
    ):
        st.button('Login', icon=':material/login:', key='login_btn')
        st.toggle('Show browser', value=False, key='show_browser')
    img_area = st.empty()
    msg_area = st.empty()

    if st.session_state.login_btn:
        # crawl qr code
        with st.spinner('Crawling QR code...'):
            res = httpx.get(
                f'{base_url}/login_qr_code', 
                params={'headless': not st.session_state.show_browser}
            )
            try:
                res.raise_for_status()
            except Exception as e:
                st.exception(e)
                httpx.post(f'{base_url}/stop_browser')
                return
            img_area.image(base64.b64decode(res.json()['qr_code']))
        
        # check login status
        is_login = False
        start = time.time()
        while not is_login and time.time() < start + 30:
            res = httpx.get(f'{base_url}/login_status')
            try:
                res.raise_for_status()
            except Exception as e:
                st.exception(e)
                httpx.post(f'{base_url}/stop_browser')
                return
            is_login = res.json()['is_login']
            if is_login:
                httpx.post(f'{base_url}/save_cookie')
                break
            time_left = int(30 - (time.time() - start))
            msg_area.text(f'Expire in {time_left} seconds')
            time.sleep(1)

        # chech final result
        if not is_login:
            msg_area.text('Login timeout after 30s')
        else:
            msg_area.text('Login successfully')
        img_area.empty()
        httpx.post(f'{base_url}/stop_browser')

    res = httpx.get(f'{base_url}/cookie')
    res.raise_for_status()
    st.json(res.json())


main()
