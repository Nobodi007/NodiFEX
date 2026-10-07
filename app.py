from __future__ import annotations

from typing import Any, Dict


# =========================================================
# CONFIG
# =========================================================

def load_config(secrets) -> Dict[str, str]:
    """
    Read Settrade configuration from Streamlit Secrets.

    Expected:

    [settrade]
    app_id = "..."
    app_secret = "..."
    broker_id = "SANDBOX"
    app_code = "SANDBOX"
    derivatives_account = "Nobody-D"
    """

    default_config = {
        "app_id": "",
        "app_secret": "",
        "broker_id": "SANDBOX",
        "app_code": "SANDBOX",
        "derivatives_account": "Nobody-D",
    }

    try:
        cfg = secrets.get("settrade")

        if not cfg:
            return default_config

        return {
            "app_id": str(cfg.get("app_id", "")).strip(),
            "app_secret": str(cfg.get("app_secret", "")).strip(),
            "broker_id": str(
                cfg.get("broker_id", "SANDBOX")
            ).strip(),
            "app_code": str(
                cfg.get("app_code", "SANDBOX")
            ).strip(),
            "derivatives_account": str(
                cfg.get(
                    "derivatives_account",
                    "Nobody-D",
                )
            ).strip(),
        }

    except Exception:
        return default_config


# =========================================================
# ERROR SERIALIZER
# =========================================================

def _error_details(exc: Exception) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "type": type(exc).__name__,
        "message": str(exc),
    }

    for attr in (
        "code",
        "status_code",
    ):
        try:
            value = getattr(exc, attr, None)

            if value is not None:
                result[attr] = value

        except Exception:
            pass

    try:
        response = getattr(exc, "response", None)

        if response is not None:

            try:
                result["response_status"] = (
                    response.status_code
                )
            except Exception:
                pass

            try:
                text = response.text

                if text:
                    result["response_text"] = text[:3000]

            except Exception:
                pass

    except Exception:
        pass

    return result


# =========================================================
# SDK INFO
# =========================================================

def _sdk_metadata() -> Dict[str, Any]:
    result = {
        "package": "settrade-v2",
        "version": "unknown",
        "import": "ERROR",
    }

    try:
        import importlib.metadata as metadata

        try:
            result["version"] = metadata.version(
                "settrade-v2"
            )
        except Exception:
            pass

    except Exception:
        pass

    return result


# =========================================================
# MAIN READ-ONLY CONNECTOR
# =========================================================

def connect_read_only(secrets) -> Dict[str, Any]:

    # -----------------------------------------------------
    # IMPORTANT:
    # This function must NEVER crash the Streamlit page.
    # Any connection problem becomes diagnostic data.
    # -----------------------------------------------------

    state: Dict[str, Any] = {
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

        "errors": [],
    }

    # =====================================================
    # 1. CONFIGURATION
    # =====================================================

    try:
        cfg = load_config(secrets)

    except Exception as exc:
        state["errors"].append({
            "stage": "Configuration",
            **_error_details(exc),
        })

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
        state["errors"].append({
            "stage": "Configuration",
            "type": "ConfigurationError",
            "message": "Missing Settrade configuration.",
            "missing": missing,
        })

        return state

    state["configured"] = True

    # =====================================================
    # 2. IMPORT SDK
    # =====================================================

    try:
        from settrade_v2 import Investor

        sdk = _sdk_metadata()

        sdk["import"] = "OK"

        state["sdk"] = sdk

    except Exception as exc:
        sdk = _sdk_metadata()
        sdk["import"] = "ERROR"

        state["sdk"] = sdk

        state["errors"].append({
            "stage": "SDK Import",
            **_error_details(exc),
        })

        return state

    # =====================================================
    # 3. CREATE INVESTOR
    # =====================================================

    try:

        investor = Investor(
            app_id=cfg["app_id"],
            app_secret=cfg["app_secret"],
            broker_id=cfg["broker_id"],
            app_code=cfg["app_code"],
            is_auto_queue=False,
        )

    except Exception as exc:

        state["errors"].append({
            "stage": "Create Investor",
            **_error_details(exc),
        })

        # IMPORTANT:
        # Do NOT raise the exception.
        # The existing UI must continue rendering.

        return state

    # =====================================================
    # 4. CREATE DERIVATIVES ACCOUNT
    # =====================================================

    try:

        deri = investor.Derivatives(
            account_no=cfg["derivatives_account"]
        )

    except Exception as exc:

        state["errors"].append({
            "stage": "Create Derivatives",
            **_error_details(exc),
        })

        return state

    # =====================================================
    # 5. ACCOUNT INFO
    # =====================================================

    try:

        state["account_info"] = (
            deri.get_account_info()
        )

    except Exception as exc:

        state["errors"].append({
            "stage": "get_account_info",
            **_error_details(exc),
        })

        return state

    # Account information succeeded.
    state["connected"] = True

    # =====================================================
    # 6. PORTFOLIO
    # =====================================================

    try:

        if hasattr(deri, "get_portfolio"):

            state["portfolio"] = (
                deri.get_portfolio()
            )

    except Exception as exc:

        state["errors"].append({
            "stage": "get_portfolio",
            **_error_details(exc),
        })

    # =====================================================
    # 7. ORDERS
    # =====================================================

    try:

        if hasattr(deri, "list_orders"):

            state["orders"] = (
                deri.list_orders()
            )

    except Exception as exc:

        state["errors"].append({
            "stage": "list_orders",
            **_error_details(exc),
        })

    # =====================================================
    # 8. RETURN
    # =====================================================

    return state
