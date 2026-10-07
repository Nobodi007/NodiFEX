import json
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from services.settrade_client import connect_read_only


st.set_page_config(
    page_title="TFEX Terminal",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)


st.markdown(
    """
    <style>
        .stMainBlockContainer {
            max-width: none !important;
            width: 100% !important;
            padding: 0 !important;
        }

        section.main > div.block-container {
            max-width: none !important;
            width: 100% !important;
            padding: 0 !important;
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
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=20, show_spinner=False)
def read_settrade():
    return connect_read_only(st.secrets)


state = read_settrade()


html_path = Path(__file__).with_name("index.html")
html = html_path.read_text(encoding="utf-8")


state_json = json.dumps(
    state,
    ensure_ascii=False,
    separators=(",", ":"),
)


injection = (
    f"<script>window.__TFEX_STATE__ = {state_json};</script>"
)

html = html.replace(
    "</head>",
    injection + "</head>",
    1,
)


components.html(
    html,
    height=1400,
    scrolling=False,
)
