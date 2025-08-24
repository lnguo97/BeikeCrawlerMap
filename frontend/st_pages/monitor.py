import os
import sqlite3
import time

import streamlit as st
import httpx


def spider_control():
    base_url = os.getenv('BACKEND_URL') or 'http://localhost:8000'
    res = httpx.get(f'{base_url}/is_spider_running')
    res.raise_for_status()
    if res.json()['is_spider_running']:
        st.info('Spider is running')
        st.button(
            'Stop Spider', 
            icon=':material/stop:', 
            key='stop_spider',
            # type='secondary'
        )
    else:
        st.info('Spider is not running')
        st.button(
            'Start Spider', 
            icon=':material/play_arrow:', 
            key='start_spider',
            # type='primary'
        )
    if st.session_state.get('stop_spider'):
        res = httpx.post(f'{base_url}/stop_spider')
        res.raise_for_status()
        time.sleep(2)  # wait for the spider to stop
        st.rerun()

    if st.session_state.get('start_spider'):
        res = httpx.post(f'{base_url}/run_spider')
        res.raise_for_status()
        time.sleep(2)  # wait for the spider to start
        st.rerun()


@st.fragment(run_every=5)
def spider_monitor():
    base_url = os.getenv('BACKEND_URL') or 'http://localhost:8000'
    res = httpx.get(f'{base_url}/spider_progress')
    res.raise_for_status()
    progress = res.json()
    col1, col2, col3 = st.columns(3)
    col1.metric(
        label="District", 
        value=(
            f"{progress['district']['finished']}/"
            f"{progress['district']['total']}"
        ),
        border=True
    )
    col2.metric(
        label="Bizcircle", 
        value=(
            f"{progress['bizcircle']['finished']}/"
            f"{progress['bizcircle']['total']}"
        ),
        border=True
    )
    col3.metric(
        label="Community", 
        value=(
            f"{progress['community']['finished']}/"
            f"{progress['community']['total']}"
        ),
        border=True
    )
    res = httpx.get(f'{base_url}/spider_log')
    if res.status_code == 200:
        st.code(res.json()['spider_log'])


def main():
    st.title('Spider Monitoring')
    spider_control()
    spider_monitor()
    

main()
