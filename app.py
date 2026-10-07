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


@st.cache_data(ttl=20, show_spinner=False)
def read_settrade(_secrets):
    return connect_read_only(_secrets)


tfex_state = read_settrade(st.secrets)

html_path = Path(__file__).with_name("index.html")
html = html_path.read_text(encoding="utf-8")

state_json = json.dumps(
    tfex_state,
    ensure_ascii=False,
    default=str,
)

html = f"""
<script>
window.__TFEX_STATE__ = {state_json};
</script>

{html}
"""

components.html(
    html,
    height=2400,
    scrolling=False,
)
