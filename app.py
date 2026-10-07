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

.tfex-diag {
    padding:12px 16px;
    border:1px solid rgba(128,128,128,.25);
    border-radius:10px;
    margin:8px 0 14px;
}

.tfex-ok {
    color:#20c997;
    font-weight:700;
}

.tfex-bad {
    color:#ff6b6b;
    font-weight:700;
}

.tfex-muted {
    opacity:.75;
}
</style>
""", unsafe_allow_html=True)


# ============================================================
# SETTRADE CONNECTION
# ============================================================

def read_settrade():
    try:
        return connect_read_only(st.secrets)

    except Exception as exc:
        return {
            "configured": False,
            "connected": False,
            "sdk": {
                "package": "settrade-v2",
                "version": "unknown",
                "import": "ERROR",
            },
            "account_info": None,
            "portfolio": None,
            "orders": None,
            "errors": [
                {
                    "stage": "Application",
                    "type": type(exc).__name__,
                    "message": str(exc),
                }
            ],
        }


state = read_settrade()
cfg = load_config(st.secrets)


# ============================================================
# DIAGNOSTIC PANEL
# ============================================================

with st.expander(
    "🔌 Settrade Sandbox connection diagnostic",
    expanded=not state.get("connected", False),
):

    configured = bool(state.get("configured"))
    connected = bool(state.get("connected"))
    sdk_ok = bool(
        state.get("sdk", {}).get("import")
        and state.get("sdk", {}).get("import") != "ERROR"
    )

    st.markdown(
        f"""
        <div class="tfex-diag">
            <div>
                Environment:
                <b>{cfg.get("app_code") or "—"}</b>
            </div>

            <div>
                Broker:
                <b>{cfg.get("broker_id") or "—"}</b>
            </div>

            <div>
                Derivatives account:
                <b>{cfg.get("derivatives_account") or "—"}</b>
            </div>

            <br>

            <div>
                Secrets configured:
                <span class="{'tfex-ok' if configured else 'tfex-bad'}">
                    {'YES' if configured else 'NO'}
                </span>
            </div>

            <div>
                SDK / Import:
                <span class="{'tfex-ok' if sdk_ok else 'tfex-bad'}">
                    {state.get("sdk", {}).get("import", "ERROR")}
                </span>
            </div>

            <div>
                Connection:
                <span class="{'tfex-ok' if connected else 'tfex-bad'}">
                    {'CONNECTED' if connected else 'NOT CONNECTED'}
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


    # --------------------------------------------------------
    # Errors
    # --------------------------------------------------------

    errors = state.get("errors") or []

    if errors:

        st.error("Settrade returned an error:")

        for error in errors:

            if isinstance(error, dict):
                st.code(
                    json.dumps(
                        error,
                        ensure_ascii=False,
                        indent=2,
                        default=str,
                    ),
                    language="json",
                )
            else:
                st.code(
                    str(error),
                    language=None,
                )

    else:

        st.success(
            "Settrade read-only connection is healthy."
        )


    # --------------------------------------------------------
    # SDK metadata
    # --------------------------------------------------------

    sdk_meta = state.get("sdk") or {}

    if sdk_meta:

        st.caption(
            f"SDK package: "
            f"{sdk_meta.get('package', '—')} | "
            f"version: "
            f"{sdk_meta.get('version', '—')} | "
            f"import: "
            f"{sdk_meta.get('import', '—')}"
        )


    # --------------------------------------------------------
    # Metrics
    # --------------------------------------------------------

    c1, c2, c3 = st.columns(3)

    with c1:

        st.metric(
            "Account info",
            "OK" if state.get("account_info") else "—",
        )

    with c2:

        portfolio = state.get("portfolio")

        st.metric(
            "Portfolio",
            len(portfolio)
            if isinstance(portfolio, list)
            else ("OK" if portfolio else "—"),
        )

    with c3:

        orders = state.get("orders")

        st.metric(
            "Orders",
            len(orders)
            if isinstance(orders, list)
            else ("OK" if orders else "—"),
        )


    st.caption(
        "Read-only mode. "
        "No order placement or cancellation is implemented."
    )


    # --------------------------------------------------------
    # Refresh
    # --------------------------------------------------------

    if st.button(
        "🔄 Refresh Settrade connection",
        key="refresh_settrade",
    ):

        st.rerun()


# ============================================================
# EXISTING TRADING TERMINAL
# ============================================================

html_path = Path(__file__).with_name("index.html")

html = html_path.read_text(
    encoding="utf-8"
)


# ============================================================
# INJECT TFEX STATE
# ============================================================

state_json = json.dumps(
    state,
    ensure_ascii=False,
    separators=(",", ":"),
    default=str,
)


html = html.replace(
    "</head>",
    (
        f"<script>"
        f"window.__TFEX_STATE__ = {state_json};"
        f"</script>"
        f"</head>"
    ),
    1,
)


# ============================================================
# RENDER ORIGINAL TERMINAL
# ============================================================

components.html(
    html,
    height=2400,
    scrolling=False,
)
