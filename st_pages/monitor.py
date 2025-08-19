import sqlite3

import streamlit as st


st.title('Spider Monitoring')


if 'db_conn' not in st.session_state:
    st.session_state.db_conn = sqlite3.connect('data/housing_data.db')

