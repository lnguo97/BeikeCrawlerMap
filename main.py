import pathlib

import streamlit as st


pathlib.Path('config/').mkdir(parents=True, exist_ok=True)
pathlib.Path('database/').mkdir(parents=True, exist_ok=True)

st.logo('assets/logo.png')
pg = st.navigation([
    st.Page(
        "st_pages/login.py", 
        title="Login Cookies", 
        icon=':material/cookie:'
    ),
    st.Page(
        "st_pages/spider.py", 
        title="Spider Monitoring", 
        icon=':material/monitoring:'
    ),
    st.Page(
        "st_pages/analysis.py", 
        title="Data Analysis", 
        icon=':material/bar_chart:'
    ),
])
pg.run()
