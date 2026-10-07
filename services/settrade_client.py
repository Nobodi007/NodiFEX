from __future__ import annotations

from typing import Any, Dict

import streamlit as st


def load_config() -> Dict[str, Any]:
    """Load Settrade configuration from Streamlit Secrets."""

    try:
        cfg = st.secrets["settrade"]

        return {
            "app_id": str(cfg.get("app_id", "")).strip(),
            "app_secret": str(cfg.get("app_secret", "")).strip(),
            "broker_id": str(cfg.get("broker_id", "SANDBOX")).strip(),
            "app_code": str(cfg.get("app_code", "SANDBOX")).strip(),
            "derivatives_account": str(
                cfg.get("derivatives_account", "Nobody-D")
            ).strip(),
        }

    except Exception as e:
        return {
            "app_id": "",
            "app_secret": "",
            "broker_id": "SANDBOX",
            "app_code": "SANDBOX",
            "derivatives_account": "Nobody-D",
            "_error": str(e),
        }


def _error_details(exc: Exception) -> Dict[str, Any]:
    """Extract useful information from Settrade/API exceptions."""

    details: Dict[str, Any] = {
        "type": type(exc).__name__,
        "message": str(exc),
    }

    for attr in ("code", "status_code"):
        value = getattr(exc, attr, None)
        if value is not None:
            details[attr] = value

    response = getattr(exc, "response", None)

    if response is not None:
        try:
            details["response_status"] = response.status_code
        except Exception:
            pass

        try:
            details["response_text"] = response.text[:2000]
        except Exception:
            pass

    return details


def connect_read_only() -> Dict[str, Any]:
    """
    Connect to Settrade Sandbox in READ-ONLY mode.

    This function intentionally does NOT:
    - place orders
    - cancel orders
    - modify positions
    - submit PIN

    It only tests the connection and reads account data.
    """

    state: Dict[str, Any] = {
        "connected": False,
        "environment": "SANDBOX",
        "broker_id": "",
        "app_code": "",
        "account": "",
        "stages": [],
        "errors": [],
        "account_info": None,
        "portfolio": None,
        "orders": None,
    }

    # ---------------------------------------------------------
    # STAGE 1 — Configuration
    # ---------------------------------------------------------

    cfg = load_config()

    state["broker_id"] = cfg["broker_id"]
    state["app_code"] = cfg["app_code"]
    state["account"] = cfg["derivatives_account"]

    if cfg.get("_error"):
        error = {
            "stage": "1. Configuration",
            "error": cfg["_error"],
        }

        state["stages"].append({
            "stage": "1. Configuration",
            "status": "FAIL",
        })

        state["errors"].append(error)

        return state

    required = [
        "app_id",
        "app_secret",
        "broker_id",
        "app_code",
        "derivatives_account",
    ]

    missing = [
        key
        for key in required
        if not cfg.get(key)
    ]

    if missing:
        state["stages"].append({
            "stage": "1. Configuration",
            "status": "FAIL",
        })

        state["errors"].append({
            "stage": "1. Configuration",
            "error": "Missing configuration",
            "missing": missing,
        })

        return state

    state["stages"].append({
        "stage": "1. Configuration",
        "status": "OK",
    })

    # ---------------------------------------------------------
    # STAGE 2 — Import SDK
    # ---------------------------------------------------------

    try:
        from settrade_v2 import Investor

        state["stages"].append({
            "stage": "2. Import settrade_v2",
            "status": "OK",
        })

    except Exception as e:
        state["stages"].append({
            "stage": "2. Import settrade_v2",
            "status": "FAIL",
        })

        state["errors"].append({
            "stage": "2. Import settrade_v2",
            **_error_details(e),
        })

        return state

    # ---------------------------------------------------------
    # STAGE 3 — Create Investor
    # ---------------------------------------------------------

    try:
        investor = Investor(
            app_id=cfg["app_id"],
            app_secret=cfg["app_secret"],
            broker_id=cfg["broker_id"],
            app_code=cfg["app_code"],
            is_auto_queue=False,
        )

        state["stages"].append({
            "stage": "3. Create Investor",
            "status": "OK",
        })

    except Exception as e:
        state["stages"].append({
            "stage": "3. Create Investor",
            "status": "FAIL",
        })

        state["errors"].append({
            "stage": "3. Create Investor",
            **_error_details(e),
        })

        return state

    # ---------------------------------------------------------
    # STAGE 4 — Create Derivatives client
    # ---------------------------------------------------------

    try:
        deri = investor.Derivatives(
            account_no=cfg["derivatives_account"]
        )

        state["stages"].append({
            "stage": "4. Create Derivatives",
            "status": "OK",
        })

    except Exception as e:
        state["stages"].append({
            "stage": "4. Create Derivatives",
            "status": "FAIL",
        })

        state["errors"].append({
            "stage": "4. Create Derivatives",
            **_error_details(e),
        })

        return state

    # ---------------------------------------------------------
    # STAGE 5 — Account information
    # ---------------------------------------------------------

    try:
        account_info = deri.get_account_info()

        state["account_info"] = account_info

        state["stages"].append({
            "stage": "5. get_account_info",
            "status": "OK",
        })

        # Connection is considered valid once account info works.
        state["connected"] = True

    except Exception as e:
        state["stages"].append({
            "stage": "5. get_account_info",
            "status": "FAIL",
        })

        state["errors"].append({
            "stage": "5. get_account_info",
            **_error_details(e),
        })

        return state

    # ---------------------------------------------------------
    # STAGE 6 — Portfolio
    # ---------------------------------------------------------

    try:
        portfolio = deri.get_portfolio()

        state["portfolio"] = portfolio

        state["stages"].append({
            "stage": "6. get_portfolio",
            "status": "OK",
        })

    except Exception as e:
        state["stages"].append({
            "stage": "6. get_portfolio",
            "status": "FAIL",
        })

        state["errors"].append({
            "stage": "6. get_portfolio",
            **_error_details(e),
        })

    # ---------------------------------------------------------
    # STAGE 7 — Orders
    # ---------------------------------------------------------

    try:
        orders = deri.list_orders()

        state["orders"] = orders

        state["stages"].append({
            "stage": "7. list_orders",
            "status": "OK",
        })

    except Exception as e:
        state["stages"].append({
            "stage": "7. list_orders",
            "status": "FAIL",
        })

        state["errors"].append({
            "stage": "7. list_orders",
            **_error_details(e),
        })

    return state
