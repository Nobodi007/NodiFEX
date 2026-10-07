from __future__ import annotations

from typing import Any


def _clean(value: Any) -> Any:
    """Convert SDK objects into JSON-safe Python values."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, dict):
        return {str(k): _clean(v) for k, v in value.items()}

    if isinstance(value, (list, tuple)):
        return [_clean(v) for v in value]

    if hasattr(value, "to_dict"):
        try:
            return _clean(value.to_dict())
        except Exception:
            pass

    if hasattr(value, "__dict__"):
        try:
            return _clean(vars(value))
        except Exception:
            pass

    return str(value)


def load_config(secrets) -> dict:
    """Read Settrade config from Streamlit secrets."""

    try:
        cfg = secrets.get("settrade", {})
    except Exception:
        cfg = {}

    if not isinstance(cfg, dict):
        cfg = {}

    def pick(name: str, default: str = "") -> str:
        value = cfg.get(name)

        if value is None:
            value = secrets.get(name, default)

        return str(value or "").strip()

    return {
        "app_id": pick("app_id"),
        "app_secret": pick("app_secret"),
        "broker_id": pick("broker_id", "SANDBOX"),
        "app_code": pick("app_code", "SANDBOX"),
        "derivatives_account": pick(
            "derivatives_account",
            "Nobody-D",
        ),
    }


def _error_details(exc: Exception) -> dict:
    """Extract SettradeError / HTTP error information."""

    result = {
        "type": type(exc).__name__,
        "message": str(exc),
        "code": getattr(exc, "code", None),
        "status_code": getattr(exc, "status_code", None),
    }

    response = getattr(exc, "response", None)

    if response is not None:
        try:
            result["http_status"] = response.status_code
        except Exception:
            pass

        try:
            result["response_text"] = response.text[:1000]
        except Exception:
            pass

    return result


def connect_read_only(secrets) -> dict:
    """
    Connect to Settrade V2 Sandbox in READ-ONLY mode.

    Diagnostic stages:
      1. import settrade_v2
      2. create Investor
      3. create Derivatives account
      4. get_account_info
      5. get_portfolio
      6. list_orders

    No order placement/cancel operation is performed.
    """

    config = load_config(secrets)

    state = {
        "configured": False,
        "connected": False,
        "environment": "SANDBOX",
        "broker_id": config["broker_id"],
        "app_code": config["app_code"],
        "account": config["derivatives_account"],
        "sdk_import": None,
        "stages": [],
        "account_info": {},
        "portfolio": [],
        "orders": [],
        "errors": [],
    }

    # ---------------------------------------------------------
    # Configuration
    # ---------------------------------------------------------

    missing = []

    if not config["app_id"]:
        missing.append("app_id")

    if not config["app_secret"]:
        missing.append("app_secret")

    if not config["derivatives_account"]:
        missing.append("derivatives_account")

    if missing:
        state["errors"].append({
            "stage": "configuration",
            "message": "Missing Streamlit Secret(s): "
                       + ", ".join(missing),
        })

        state["stages"].append({
            "name": "Configuration",
            "status": "ERROR",
            "message": "Missing: " + ", ".join(missing),
        })

        return state

    state["configured"] = True

    state["stages"].append({
        "name": "Configuration",
        "status": "OK",
        "message": "Secrets configured",
    })

    # ---------------------------------------------------------
    # 1. Import SDK
    # ---------------------------------------------------------

    try:
        import settrade_v2

        from settrade_v2 import Investor

        state["sdk_import"] = "settrade_v2"

        state["stages"].append({
            "name": "Import settrade_v2",
            "status": "OK",
            "message": "SDK imported successfully",
        })

    except Exception as exc:
        details = _error_details(exc)

        state["errors"].append({
            "stage": "import",
            **details,
        })

        state["stages"].append({
            "name": "Import settrade_v2",
            "status": "ERROR",
            "message": details["message"],
        })

        return state

    # ---------------------------------------------------------
    # 2. Create Investor
    # ---------------------------------------------------------

    try:
        investor = Investor(
            app_id=config["app_id"],
            app_secret=config["app_secret"],
            broker_id=config["broker_id"],
            app_code=config["app_code"],
            is_auto_queue=False,
        )

        state["stages"].append({
            "name": "Create Investor",
            "status": "OK",
            "message": "Investor initialized",
        })

    except Exception as exc:
        details = _error_details(exc)

        state["errors"].append({
            "stage": "investor_initialization",
            **details,
        })

        state["stages"].append({
            "name": "Create Investor",
            "status": "ERROR",
            "message": details["message"],
            "code": details["code"],
            "status_code": details["status_code"],
        })

        return state

    # ---------------------------------------------------------
    # 3. Create Derivatives account
    # ---------------------------------------------------------

    try:
        deri = investor.Derivatives(
            account_no=config["derivatives_account"]
        )

        state["stages"].append({
            "name": "Create Derivatives",
            "status": "OK",
            "message": (
                "Account: "
                + config["derivatives_account"]
            ),
        })

    except Exception as exc:
        details = _error_details(exc)

        state["errors"].append({
            "stage": "derivatives_initialization",
            **details,
        })

        state["stages"].append({
            "name": "Create Derivatives",
            "status": "ERROR",
            "message": details["message"],
            "code": details["code"],
            "status_code": details["status_code"],
        })

        return state

    # ---------------------------------------------------------
    # 4. get_account_info
    # ---------------------------------------------------------

    try:
        account_info = deri.get_account_info()

        state["account_info"] = _clean(account_info)

        state["stages"].append({
            "name": "get_account_info",
            "status": "OK",
            "message": "Account information received",
        })

        state["connected"] = True

    except Exception as exc:
        details = _error_details(exc)

        state["errors"].append({
            "stage": "get_account_info",
            **details,
        })

        state["stages"].append({
            "name": "get_account_info",
            "status": "ERROR",
            "message": details["message"],
            "code": details["code"],
            "status_code": details["status_code"],
        })

        return state

    # ---------------------------------------------------------
    # 5. get_portfolio
    # ---------------------------------------------------------

    try:
        if hasattr(deri, "get_portfolio"):
            portfolio = deri.get_portfolio()

            portfolio = _clean(portfolio)

            if isinstance(portfolio, dict):
                portfolio = portfolio.get(
                    "data",
                    portfolio,
                )

            state["portfolio"] = portfolio

            state["stages"].append({
                "name": "get_portfolio",
                "status": "OK",
                "message": "Portfolio received",
            })

        else:
            state["stages"].append({
                "name": "get_portfolio",
                "status": "SKIP",
                "message": "SDK method not available",
            })

    except Exception as exc:
        details = _error_details(exc)

        state["errors"].append({
            "stage": "get_portfolio",
            **details,
        })

        state["stages"].append({
            "name": "get_portfolio",
            "status": "ERROR",
            "message": details["message"],
            "code": details["code"],
            "status_code": details["status_code"],
        })

    # ---------------------------------------------------------
    # 6. list_orders
    # ---------------------------------------------------------

    try:
        if hasattr(deri, "list_orders"):
            orders = deri.list_orders()

            orders = _clean(orders)

            if isinstance(orders, dict):
                orders = orders.get(
                    "data",
                    orders,
                )

            state["orders"] = orders

            state["stages"].append({
                "name": "list_orders",
                "status": "OK",
                "message": "Orders received",
            })

        else:
            state["stages"].append({
                "name": "list_orders",
                "status": "SKIP",
                "message": "SDK method not available",
            })

    except Exception as exc:
        details = _error_details(exc)

        state["errors"].append({
            "stage": "list_orders",
            **details,
        })

        state["stages"].append({
            "name": "list_orders",
            "status": "ERROR",
            "message": details["message"],
            "code": details["code"],
            "status_code": details["status_code"],
        })

    return state
