from __future__ import annotations

from typing import Any, Dict, Iterable, Optional
import json


def _clean(value: Any) -> Any:
    """Convert SDK responses into JSON-safe Python values."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, dict):
        return {str(k): _clean(v) for k, v in value.items()}

    if isinstance(value, (list, tuple, set)):
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

    try:
        json.dumps(value)
        return value
    except Exception:
        return str(value)


def _unwrap(value: Any) -> Any:
    """Unwrap common API response envelopes."""
    value = _clean(value)

    if isinstance(value, dict) and "data" in value:
        return value["data"]

    return value


def _call_first(obj: Any, names: Iterable[str]) -> tuple[Any, Optional[str]]:
    """Call the first available method name."""
    errors = []

    for name in names:
        fn = getattr(obj, name, None)

        if not callable(fn):
            continue

        try:
            return _unwrap(fn()), None
        except Exception as exc:
            errors.append(f"{name}: {exc}")

    if errors:
        return None, " | ".join(errors)

    return None, "No supported method found."


def load_config(secrets: Any) -> Dict[str, str]:
    """
    Read Settrade configuration from Streamlit secrets.

    Preferred format:

    [settrade]
    app_id = "..."
    app_secret = "..."
    broker_id = "SANDBOX"
    app_code = "SANDBOX"
    derivatives_account = "Nobody-D"
    """

    section = {}

    try:
        section = dict(secrets.get("settrade", {}))
    except Exception:
        section = {}

    def get_value(name: str, default: str = "") -> str:
        value = section.get(name)

        if value is None:
            try:
                value = secrets.get(name, default)
            except Exception:
                value = default

        if value is None:
            return default

        return str(value).strip()

    return {
        "app_id": get_value("app_id"),
        "app_secret": get_value("app_secret"),
        "broker_id": get_value("broker_id", "SANDBOX"),
        "app_code": get_value("app_code", "SANDBOX"),
        "derivatives_account": get_value("derivatives_account"),
    }


def connect_read_only(secrets: Any) -> Dict[str, Any]:
    """
    Connect to Settrade Open API in READ-ONLY mode.

    This function intentionally does NOT place, change, or cancel orders.
    """

    config = load_config(secrets)

    result: Dict[str, Any] = {
        "configured": False,
        "connected": False,
        "environment": config.get("app_code") or "SANDBOX",
        "account": config.get("derivatives_account") or "",
        "account_info": {},
        "portfolio": [],
        "orders": [],
        "errors": [],
    }

    required = [
        "app_id",
        "app_secret",
        "derivatives_account",
    ]

    missing = [key for key in required if not config.get(key)]

    if missing:
        result["errors"].append(
            "Missing Streamlit Secrets: " + ", ".join(missing)
        )
        return result

    result["configured"] = True

    try:
        from settrade.openapi import Investor
    except Exception as exc:
        result["errors"].append(
            f"Cannot import settrade SDK: {exc}"
        )
        return result

    try:
        try:
            investor = Investor(
                app_id=config["app_id"],
                app_secret=config["app_secret"],
                broker_id=config["broker_id"],
                app_code=config["app_code"],
                is_auto_queue=False,
            )
        except TypeError:
            investor = Investor(
                app_id=config["app_id"],
                app_secret=config["app_secret"],
                broker_id=config["broker_id"],
                app_code=config["app_code"],
            )

    except Exception as exc:
        result["errors"].append(
            f"Investor initialization failed: {exc}"
        )
        return result

    try:
        derivatives = investor.Derivatives(
            account_no=config["derivatives_account"]
        )
    except Exception as exc:
        result["errors"].append(
            f"Derivatives account initialization failed: {exc}"
        )
        return result

    # ---------------------------------------------------------
    # Account information
    # ---------------------------------------------------------

    account_info, account_error = _call_first(
        derivatives,
        [
            "get_account_info",
        ],
    )

    if account_error:
        result["errors"].append(
            f"Account info: {account_error}"
        )
    else:
        result["account_info"] = account_info or {}

    # ---------------------------------------------------------
    # Portfolio / positions
    # ---------------------------------------------------------

    portfolio, portfolio_error = _call_first(
        derivatives,
        [
            "get_portfolio",
        ],
    )

    if portfolio_error:
        result["errors"].append(
            f"Portfolio: {portfolio_error}"
        )
    else:
        result["portfolio"] = portfolio or []

    # ---------------------------------------------------------
    # Orders
    # ---------------------------------------------------------

    orders, orders_error = _call_first(
        derivatives,
        [
            "list_orders",
        ],
    )

    if orders_error:
        result["errors"].append(
            f"Orders: {orders_error}"
        )
    else:
        result["orders"] = orders or []

    # If account information was successfully returned,
    # consider the connection healthy.
    if account_info is not None:
        result["connected"] = True

    return result
