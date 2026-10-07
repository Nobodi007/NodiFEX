import json
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from services.settrade_client import connect_read_only, load_config


st.set_page_config(
    page_title="TFEX Terminal",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
.stMainBlockContainer { max-width:none!important; width:100%!important; padding:0!important; }
section.main > div.block-container { max-width:none!important; width:100%!important; padding:0!important; }
[data-testid="stIFrame"] { width:100%!important; }
[data-testid="stIFrame"] iframe { width:100%!important; display:block!important; border:0!important; }
.tfex-diag { padding:12px 16px; border:1px solid rgba(128,128,128,.25); border-radius:10px; margin:8px 0 14px; }
.tfex-ok { color:#20c997; font-weight:700; }
.tfex-bad { color:#ff6b6b; font-weight:700; }
.tfex-muted { opacity:.75; }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=20, show_spinner=False)
def read_settrade():
    return connect_read_only(st.secrets)


state = read_settrade()
cfg = load_config(st.secrets)

# -----------------------------
# Diagnostic panel
# -----------------------------
with st.expander("🔌 Settrade Sandbox connection diagnostic", expanded=not state.get("connected", False)):
    configured = bool(state.get("configured"))
    connected = bool(state.get("connected"))
    sdk_ok = not any("Cannot import settrade SDK" in str(e) for e in state.get("errors", []))
    account_ok = bool(state.get("account_info")) or connected

    st.markdown(
        f"""
        <div class="tfex-diag">
            <div>Environment: <b>{cfg.get("app_code") or "—"}</b></div>
            <div>Broker: <b>{cfg.get("broker_id") or "—"}</b></div>
            <div>Derivatives account: <b>{cfg.get("derivatives_account") or "—"}</b></div>
            <br>
            <div>Secrets configured:
                <span class="{'tfex-ok' if configured else 'tfex-bad'}">
                {'YES' if configured else 'NO'}
                </span>
            </div>
            <div>SDK / Investor:
                <span class="{'tfex-ok' if sdk_ok else 'tfex-bad'}">
                {'OK' if sdk_ok else 'ERROR'}
                </span>
            </div>
            <div>Connection:
                <span class="{'tfex-ok' if connected else 'tfex-bad'}">
                {'CONNECTED' if connected else 'NOT CONNECTED'}
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    errors = state.get("errors") or []
    if errors:
        st.error("Settrade returned an error:")
        for error in errors:
            st.code(str(error), language=None)
    else:
        st.success("Settrade read-only connection is healthy.")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Account info", "OK" if state.get("account_info") else "—")
    with c2:
        portfolio = state.get("portfolio")
        st.metric("Portfolio", len(portfolio) if isinstance(portfolio, list) else ("OK" if portfolio else "—"))
    with c3:
        orders = state.get("orders")
        st.metric("Orders", len(orders) if isinstance(orders, list) else ("OK" if orders else "—"))

    st.caption("Read-only mode. No order placement or cancellation is implemented.")

    if st.button("🔄 Refresh Settrade connection", key="refresh_settrade"):
        st.cache_data.clear()
        st.rerun()


# -----------------------------
# Existing trading terminal
# -----------------------------
html_path = Path(__file__).with_name("index.html")
html = html_path.read_text(encoding="utf-8")

state_json = json.dumps(
    state,
    ensure_ascii=False,
    separators=(",", ":"),
)

html = html.replace(
    "</head>",
    f"<script>window.__TFEX_STATE__ = {state_json};</script></head>",
    1,
)

# components.html is retained because it executes the existing terminal's
# JavaScript. st.html/st.iframe do not provide an equivalent local HTML
# execution path for this app.
components.html(html, height=2400, scrolling=False)
