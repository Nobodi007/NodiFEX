from __future__ import annotations

from typing import Any, Dict


def load_config(secrets) -> Dict[str, str]:
    """
    Load Settrade configuration from Streamlit secrets.

    Expected:

    [settrade]
    app_id = "..."
    app_secret = "..."
    broker_id = "SANDBOX"
    app_code = "SANDBOX"
    derivatives_account = "Nobody-D"
    """

    try:
        cfg = secrets.get("settrade", {})

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
        return {
            "app_id": "",
            "app_secret": "",
            "broker_id": "SANDBOX",
            "app_code": "SANDBOX",
            "derivatives_account": "Nobody-D",
        }


def _error_details(exc: Exception) -> Dict[str, Any]:
    """
    Convert an exception into safe diagnostic information.
    Never expose app_secret.
    """

    result: Dict[str, Any] = {
        "type": type(exc).__name__,
        "message": str(exc),
    }

    for attr in (
        "code",
        "status_code",
    ):
        value = getattr(exc, attr, None)

        if value is not None:
            result[attr] = value

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

    return result


def _sdk_metadata() -> Dict[str, Any]:
    """
    Detect installed Settrade SDK without creating
    an Investor connection.
    """

    try:
        import importlib.metadata as metadata

        try:
            version = metadata.version(
                "settrade-v2"
            )
        except Exception:
            version = "unknown"

        return {
            "package": "settrade-v2",
            "version": version,
            "import": "settrade_v2",
        }

    except Exception:
        return {
            "package": "settrade-v2",
            "version": "unknown",
            "import": "ERROR",
        }


def connect_read_only(secrets) -> Dict[str, Any]:
    """
    Read-only Settrade connection.

    IMPORTANT:
    This function does NOT place orders.
    This function does NOT cancel orders.
    This function does NOT send PIN.

    It only:
      1. validates configuration
      2. imports SDK
      3. creates Investor
      4. creates Derivatives client
      5. reads account info
      6. reads portfolio
      7. reads orders
    """

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

    # ========================================================
    # 1. CONFIGURATION
    # ========================================================

    cfg = load_config(secrets)

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

        state["errors"].append(
            {
                "stage": "Configuration",
                "type": "ConfigurationError",
                "message": (
                    "Missing required Settrade "
                    "configuration."
                ),
                "missing": missing,
            }
        )

        return state

    state["configured"] = True

    # ========================================================
    # 2. IMPORT SDK
    # ========================================================

    try:

        import settrade_v2

        from settrade_v2 import Investor

        state["sdk"] = _sdk_metadata()

        state["sdk"]["import"] = (
            "settrade_v2"
        )

    except Exception as exc:

        state["sdk"] = _sdk_metadata()

        state["errors"].append(
            {
                "stage": "SDK Import",
                **_error_details(exc),
            }
        )

        return state

    # ========================================================
    # 3. CREATE INVESTOR
    # ========================================================

    try:

        investor = Investor(
            app_id=cfg["app_id"],
            app_secret=cfg["app_secret"],
            broker_id=cfg["broker_id"],
            app_code=cfg["app_code"],
            is_auto_queue=False,
        )

    except Exception as exc:

        state["errors"].append(
            {
                "stage": "Create Investor",
                **_error_details(exc),
            }
        )

        return state

    # ========================================================
    # 4. CREATE DERIVATIVES CLIENT
    # ========================================================

    try:

        deri = investor.Derivatives(
            account_no=cfg[
                "derivatives_account"
            ]
        )

    except Exception as exc:

        state["errors"].append(
            {
                "stage": "Create Derivatives",
                **_error_details(exc),
            }
        )

        return state

    # ========================================================
    # 5. ACCOUNT INFO
    # ========================================================

    try:

        account_info = (
            deri.get_account_info()
        )

        state["account_info"] = account_info

    except Exception as exc:

        state["errors"].append(
            {
                "stage": "get_account_info",
                **_error_details(exc),
            }
        )

        return state

    # At this point authentication / account access
    # has succeeded.

    state["connected"] = True

    # ========================================================
    # 6. PORTFOLIO
    # ========================================================

    try:

        state["portfolio"] = (
            deri.get_portfolio()
        )

    except Exception as exc:

        state["errors"].append(
            {
                "stage": "get_portfolio",
                **_error_details(exc),
            }
        )

    # ========================================================
    # 7. ORDERS
    # ========================================================

    try:

        state["orders"] = (
            deri.list_orders()
        )

    except Exception as exc:

        state["errors"].append(
            {
                "stage": "list_orders",
                **_error_details(exc),
            }
        )

    return state
