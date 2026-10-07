import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path

st.set_page_config(page_title='TFEX Terminal', page_icon='📈', layout='wide', initial_sidebar_state='collapsed')

# Streamlit puts components inside a centered/max-width block by default.
# The terminal itself is designed as a full-width trading workspace, so remove
# the parent padding/max-width and let the iframe stretch across the viewport.
st.markdown("""
<style>
    /* Current Streamlit layout */
    .stMainBlockContainer {
        max-width: none !important;
        width: 100% !important;
        padding-left: 0 !important;
        padding-right: 0 !important;
        padding-top: 0 !important;
    }
    /* Older Streamlit layout fallback */
    section.main > div.block-container {
        max-width: none !important;
        width: 100% !important;
        padding-left: 0 !important;
        padding-right: 0 !important;
        padding-top: 0 !important;
    }
    [data-testid="stIFrame"] {
        width: 100% !important;
    }
    [data-testid="stIFrame"] iframe {
        width: 100% !important;
        display: block !important;
        border: 0 !important;
    }
</style>
""", unsafe_allow_html=True)

html = Path(__file__).with_name('index.html').read_text(encoding='utf-8')
components.html(html, height=1000, scrolling=False)

