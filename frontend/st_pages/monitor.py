import os
import sqlite3
import time

import streamlit as st
import requests


base_url = os.getenv('BACKEND_URL') or 'http://localhost:8000'


def page_header():
    st.session_state.city_list = requests.get(f'{base_url}/spider_log').json()
    with st.container(horizontal=True, vertical_alignment='bottom'):
        st.title('Spider Monitoring')
        st.selectbox(
            'Choose city:', 
            options=st.session_state.city_list.keys(),
            key='selected_city'
        )


@st.fragment(run_every=5)
def spider_control():
    res = requests.get(f'{base_url}/is_spider_running')
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
        res = requests.post(f'{base_url}/stop_spider')
        res.raise_for_status()
        time.sleep(2)  # wait for the spider to stop
        st.rerun()

    if st.session_state.get('start_spider'):
        res = requests.post(f'{base_url}/run_spider')
        res.raise_for_status()
        time.sleep(2)  # wait for the spider to start
        st.rerun()


@st.fragment(run_every=5)
def spider_progress():
    st.subheader('Spider Progress')
    res = requests.get(f'{base_url}/spider_progress')
    res.raise_for_status()
    progress = res.json()
    st.text(f"Data Date: {progress['ds']}")
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


@st.fragment(run_every=5)
def spider_log():
    st.subheader('Spider Log')
    result = requests.get(f'{base_url}/spider_log').json()
    spider_log = result['spider_log']
    ds = result['ds']
    st.text(f"Data Date: {ds}")
    if not spider_log:
        st.text(f'Spider for date {ds} has not started')
    else:
        st.download_button(
            label=f"Download spider log",
            data=spider_log,
            file_name=f"spider_{ds}.txt",
            on_click="ignore",
            icon=":material/download:",
        )


def main():
    
    spider_control()
    spider_progress()
    spider_log()
    

main()
