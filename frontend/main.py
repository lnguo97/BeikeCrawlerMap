import pathlib

import streamlit as st


st.logo('assets/logo.png')
st.set_page_config(page_title='Beike Crawler', layout='centered')
pg = st.navigation([
    st.Page(
        "st_pages/login.py", 
        title="Login Cookies", 
        icon=':material/cookie:'
    ),
    st.Page(
        "st_pages/monitor.py", 
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
