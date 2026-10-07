from __future__ import annotations

import json

import streamlit as st
import streamlit.components.v1 as components

from services.settrade_client import connect_read_only


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="NodiFEX",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# LOAD SETTRADE
# ============================================================

try:
    state = connect_read_only()
except Exception as e:
    state = {
        "connected": False,
        "environment": "SANDBOX",
        "broker_id": "SANDBOX",
        "app_code": "SANDBOX",
        "account": "Nobody-D",
        "stages": [],
        "errors": [
            {
                "stage": "Application",
                "type": type(e).__name__,
                "message": str(e),
            }
        ],
        "account_info": None,
        "portfolio": None,
        "orders": None,
    }


# ============================================================
# NORMALIZE STATE
# ============================================================

if not isinstance(state, dict):
    state = {
        "connected": False,
        "environment": "SANDBOX",
        "broker_id": "SANDBOX",
        "app_code": "SANDBOX",
        "account": "Nobody-D",
        "stages": [],
        "errors": [
            {
                "stage": "Application",
                "type": "InvalidState",
                "message": "Settrade client returned an invalid state.",
            }
        ],
        "account_info": None,
        "portfolio": None,
        "orders": None,
    }


state.setdefault("connected", False)
state.setdefault("environment", "SANDBOX")
state.setdefault("broker_id", "SANDBOX")
state.setdefault("app_code", "SANDBOX")
state.setdefault("account", "Nobody-D")
state.setdefault("stages", [])
state.setdefault("errors", [])
state.setdefault("account_info", None)
state.setdefault("portfolio", None)
state.setdefault("orders", None)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown(
        """
        # NodiFEX

        TFEX Trading Journal
        """
    )

    st.divider()

    page = st.radio(
        "Navigation",
        [
            "Dashboard",
            "Orders",
            "Positions",
            "Journal",
            "Analytics",
        ],
        index=0,
    )

    st.divider()

    if state.get("connected"):
        st.success("TFEX CONNECTED")
    else:
        st.warning("TFEX NOT CONNECTED")

    st.caption("READ-ONLY MODE")


# ============================================================
# TOP STATUS
# ============================================================

if state.get("connected"):
    st.success(
        "ACCOUNT MODE: LIVE ACCOUNT SHELL • "
        "TFEX API CONNECTED • READ-ONLY"
    )
else:
    st.warning(
        "ACCOUNT MODE: LIVE ACCOUNT SHELL • "
        "TFEX API NOT CONNECTED • READ-ONLY"
    )


# ============================================================
# SETTRADE DIAGNOSTIC
# ============================================================

with st.expander(
    "🔧 Settrade Sandbox Diagnostic",
    expanded=not state.get("connected"),
):

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.caption("Environment")
        st.markdown(
            f"### {state.get('environment', '-')}"
        )

    with col2:
        st.caption("Broker")
        st.markdown(
            f"### {state.get('broker_id', '-')}"
        )

    with col3:
        st.caption("Account")
        st.markdown(
            f"### {state.get('account', '-')}"
        )

    with col4:
        st.caption("Connection")

        if state.get("connected"):
            st.markdown("### 🟢 CONNECTED")
        else:
            st.markdown("### 🔴 NOT CONNECTED")

    st.divider()

    st.markdown("### Connection Stages")

    stages = state.get("stages", [])

    if not stages:
        st.info("No diagnostic stages returned.")
    else:
        for s in stages:

            # รองรับทั้ง format ใหม่และ format เก่า
            stage_name = (
                s.get("stage")
                or s.get("name")
                or "Unknown stage"
            )

            status = (
                s.get("status")
                or "UNKNOWN"
            )

            status = str(status).upper()

            if status == "OK":
                icon = "✅"
            elif status in ("FAIL", "ERROR"):
                icon = "❌"
            else:
                icon = "⚠️"

            st.write(
                f"{icon} **{stage_name}** — {status}"
            )

    # --------------------------------------------------------
    # ERROR DETAILS
    # --------------------------------------------------------

    errors = state.get("errors", [])

    if errors:
        st.divider()

        st.markdown("### Error Details")

        for error in errors:

            if not isinstance(error, dict):
                st.error(str(error))
                continue

            stage = error.get(
                "stage",
                "Unknown stage",
            )

            message = (
                error.get("message")
                or error.get("error")
                or "Unknown error"
            )

            error_type = error.get(
                "type",
                "",
            )

            if error_type:
                st.error(
                    f"{stage}\n\n"
                    f"{error_type}: {message}"
                )
            else:
                st.error(
                    f"{stage}\n\n"
                    f"{message}"
                )

            extra = {
                key: value
                for key, value in error.items()
                if key not in {
                    "stage",
                    "message",
                    "error",
                    "type",
                }
            }

            if extra:
                st.json(extra)

    # --------------------------------------------------------
    # CONFIG STATUS
    # --------------------------------------------------------

    st.divider()

    st.markdown("### Configuration")

    st.write(
        "Secrets configured:",
        "YES" if state.get("broker_id") else "NO",
    )

    st.caption(
        "Application Secret is never displayed."
    )


# ============================================================
# PREPARE DATA FOR HTML TERMINAL
# ============================================================

terminal_state = {
    "connected": bool(state.get("connected")),

    "environment": state.get(
        "environment",
        "SANDBOX",
    ),

    "broker_id": state.get(
        "broker_id",
        "",
    ),

    "account": state.get(
        "account",
        "",
    ),

    "account_info": state.get(
        "account_info"
    ),

    "portfolio": state.get(
        "portfolio"
    ),

    "orders": state.get(
        "orders"
    ),

    "stages": state.get(
        "stages",
        []
    ),

    "errors": state.get(
        "errors",
        []
    ),
}


# ============================================================
# PAGE CONTENT
# ============================================================

if page == "Dashboard":

    st.title("Dashboard")

    st.caption(
        "Read-only until TFEX API is connected."
    )

    # --------------------------------------------------------
    # Account cards
    # --------------------------------------------------------

    c1, c2, c3, c4 = st.columns(4)

    account_info = state.get("account_info")

    if not isinstance(account_info, dict):
        account_info = {}

    with c1:
        st.metric(
            "Portfolio Value",
            "—",
        )

    with c2:
        st.metric(
            "Equity",
            "—",
        )

    with c3:
        st.metric(
            "Margin Used",
            "—",
        )

    with c4:
        st.metric(
            "Unrealized P/L",
            "—",
        )

    st.divider()

    # --------------------------------------------------------
    # Connection status
    # --------------------------------------------------------

    if state.get("connected"):

        st.success(
            "Settrade account connected successfully."
        )

    else:

        st.info(
            "No live account data yet. "
            "Waiting for successful TFEX API connection."
        )

    # --------------------------------------------------------
    # Positions summary
    # --------------------------------------------------------

    st.subheader("Open Positions")

    portfolio = state.get("portfolio")

    if portfolio:

        st.json(portfolio)

    else:

        st.info(
            "0 positions\n\n"
            "No open positions from connected account."
        )

    # --------------------------------------------------------
    # Orders summary
    # --------------------------------------------------------

    st.subheader("Orders")

    orders = state.get("orders")

    if orders:

        st.json(orders)

    else:

        st.info(
            "0 orders\n\n"
            "No orders returned by account."
        )


elif page == "Orders":

    st.title("Orders")

    st.caption(
        "Read-only. No order placement or cancellation."
    )

    orders = state.get("orders")

    if orders:

        st.json(orders)

    else:

        st.info(
            "No orders returned by connected account."
        )


elif page == "Positions":

    st.title("Positions")

    st.caption(
        "Live account positions will appear here "
        "after TFEX API connection."
    )

    portfolio = state.get("portfolio")

    if portfolio:

        st.json(portfolio)

    else:

        st.info(
            "No open positions from connected account."
        )


elif page == "Journal":

    st.title("Trade Journal")

    st.caption(
        "Trade journal will populate from synced "
        "TFEX trades."
    )

    st.info(
        "No trade data — waiting for TFEX account connection."
    )


elif page == "Analytics":

    st.title("Analytics")

    st.caption(
        "Analytics will populate from real closed trades."
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            "Win Rate",
            "—",
        )

    with c2:
        st.metric(
            "Net P/L",
            "—",
        )

    with c3:
        st.metric(
            "Profit Factor",
            "—",
        )

    with c4:
        st.metric(
            "Closed Trades",
            "0",
        )

    st.divider()

    st.info(
        "No trade data — waiting for TFEX account connection."
    )


# ============================================================
# EXISTING HTML TERMINAL
# ============================================================

try:

    with open(
        "index.html",
        "r",
        encoding="utf-8",
    ) as f:

        html = f.read()

    # Inject state before existing JavaScript runs.
    state_script = f"""
    <script>
        window.__TFEX_STATE__ = {json.dumps(
            terminal_state,
            ensure_ascii=False,
            default=str,
        )};
    </script>
    """

    html = state_script + html

    st.divider()

    components.html(
        html,
        height=1200,
        scrolling=True,
    )

except FileNotFoundError:

    st.error(
        "index.html not found. "
        "Make sure index.html is in the repository root."
    )

except Exception as e:

    st.error(
        f"Unable to render index.html: "
        f"{type(e).__name__}: {e}"
    )
