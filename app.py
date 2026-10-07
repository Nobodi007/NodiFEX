import json
import platform
from pathlib import Path

import requests
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


@st.cache_data(ttl=30, show_spinner=False)
def probe_settrade_network():
    """Probe the exact SDK version endpoint from the deployed Streamlit runtime.

    This does not use credentials. It is intentionally separate from
    connect_read_only() so we can distinguish a network/WAF 403 from an
    authentication or account problem.
    """
    url = "https://open-api-test.settrade.com/sdk-open-api/sdk-version.json"

    try:
        import settrade_v2

        sdk_version = getattr(settrade_v2, "__version__", "unknown")
        ua = (
            f"SettradeOpenApiSdkV2Python{platform.python_version()}"
            f"_x{platform.architecture()[0].replace('bit', '')}/{sdk_version}"
        )

        response = requests.get(
            url,
            headers={
                "User-Agent": ua,
                "Content-Type": "application/json",
            },
            timeout=20,
        )

        return {
            "ok": response.ok,
            "status": response.status_code,
            "reason": response.reason,
            "url": url,
            "python": platform.python_version(),
            "platform": platform.platform(),
            "machine": platform.machine(),
            "architecture": platform.architecture()[0],
            "sdk_version": sdk_version,
            "user_agent": ua,
            "body": response.text[:1500],
            "error": None,
        }
    except Exception as exc:
        return {
            "ok": False,
            "status": None,
            "reason": None,
            "url": url,
            "python": platform.python_version(),
            "platform": platform.platform(),
            "machine": platform.machine(),
            "architecture": platform.architecture()[0],
            "sdk_version": None,
            "user_agent": None,
            "body": None,
            "error": f"{type(exc).__name__}: {exc}",
        }


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
    sdk_ok = bool(state.get("sdk"))
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
            <div>SDK / Import:
                <span class="{'tfex-ok' if sdk_ok else 'tfex-bad'}">
                {state.get('sdk', {}).get('import', 'ERROR') if sdk_ok else 'ERROR'}
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

    sdk_meta = state.get("sdk") or {}
    if sdk_meta:
        st.caption(f"SDK package: {sdk_meta.get('package', '—')} | version: {sdk_meta.get('version', '—')} | import: {sdk_meta.get('import', '—')}")

    # Cloud-side network diagnostic. This is the same version endpoint that
    # settrade-v2 checks during Investor initialization, but without secrets.
    st.divider()
    st.subheader("🌐 Settrade network diagnostic")

    probe = probe_settrade_network()

    p1, p2, p3 = st.columns(3)
    with p1:
        st.metric("SDK version", probe.get("sdk_version") or "—")
    with p2:
        status = probe.get("status")
        st.metric("Version endpoint", str(status) if status is not None else "ERROR")
    with p3:
        st.metric("Python", probe.get("python") or "—")

    if probe.get("ok"):
        st.success("Cloud runtime can reach the Settrade Sandbox version endpoint (HTTP 200).")
    elif probe.get("status") == 403:
        st.error(
            "Cloud runtime reaches Settrade, but Settrade/CDN returns HTTP 403 "
            "for the SDK version endpoint. This is not a missing-secret error."
        )
        st.info(
            "Local testing can still work while Streamlit Community Cloud fails because "
            "the app runs from Streamlit's cloud network. If this stays 403, the likely "
            "fix is network/IP allowlisting or moving the Settrade connector to a backend "
            "with an accepted/stable egress IP—not changing the App ID/secret."
        )
    elif probe.get("status") is not None:
        st.warning(
            f"Cloud runtime reached the endpoint but received HTTP {probe.get('status')} "
            f"({probe.get('reason') or 'no reason'})."
        )
    else:
        st.warning(f"Network probe failed: {probe.get('error') or 'unknown error'}")

    with st.expander("Show cloud runtime details", expanded=False):
        st.write("Platform:", probe.get("platform") or "—")
        st.write("Machine:", probe.get("machine") or "—")
        st.write("Architecture:", probe.get("architecture") or "—")
        st.write("Endpoint:", probe.get("url") or "—")
        st.write("User-Agent:", probe.get("user_agent") or "—")
        if probe.get("body"):
            st.code(probe["body"], language="json")
        if probe.get("error"):
            st.code(probe["error"], language=None)

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
