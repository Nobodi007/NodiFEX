import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path

st.set_page_config(page_title='TFEX Terminal', page_icon='📈', layout='wide', initial_sidebar_state='collapsed')
html = Path(__file__).with_name('index.html').read_text(encoding='utf-8')
components.html(html, height=2400, scrolling=False)
