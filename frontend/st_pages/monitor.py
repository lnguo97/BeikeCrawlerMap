import os
import sqlite3
import time

import streamlit as st
import httpx

@st.fragment(run_every=5)
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
    st.subheader('Spider Progress')
    base_url = os.getenv('BACKEND_URL') or 'http://localhost:8000'
    res = httpx.get(f'{base_url}/spider_progress')
    res.raise_for_status()
    progress = res.json()
    st.write(f"Data Date: {progress['ds']}")
    col1, col2 = st.columns(2)
    col1.metric(
        label="Community List", 
        value=(
            f"{progress['community_list']['finished']}/"
            f"{progress['community_list']['total']}"
        ),
        border=True
    )
    col2.metric(
        label="House List", 
        value=(
            f"{progress['house_list']['finished']}/"
            f"{progress['house_list']['total']}"
        ),
        border=True
    )
    col1, col2 = st.columns(2)
    col1.metric(
        label="Community Detail", 
        value=(
            f"{progress['community_detail']['finished']}/"
            f"{progress['community_detail']['total']}"
        ),
        border=True
    )
    col2.metric(
        label="House Detail", 
        value=(
            f"{progress['house_detail']['finished']}/"
            f"{progress['house_detail']['total']}"
        ),
        border=True
    )
    st.subheader('Spider Log')
    with st.expander('View Spider Log'):
        res = httpx.get(f'{base_url}/spider_log')
        if res.status_code == 200:
            st.code(res.json()['spider_log'])


def main():
    st.title('Spider Monitoring')
    spider_control()
    spider_monitor()
    

main()
