"""Read-only Settrade Open API connector for TFEX/derivatives.

This module intentionally exposes NO order-placement/cancel methods.
"""
from __future__ import annotations

from typing import Any, Dict, Optional


def _secret_value(cfg: Any, key: str, default: str = "") -> str:
    try:
        v = cfg.get(key, default)
    except Exception:
        try:
            v = cfg[key]
        except Exception:
            v = default
    return "" if v is None else str(v)


def load_config(secrets: Any) -> Dict[str, str]:
    """Accept either [settrade] nested secrets or flat Streamlit secrets."""
    try:
        cfg = secrets["settrade"]
    except Exception:
        cfg = secrets
    return {
        "app_id": _secret_value(cfg, "app_id") or _secret_value(secrets, "SETTRADE_APP_ID"),
        "app_secret": _secret_value(cfg, "app_secret") or _secret_value(secrets, "SETTRADE_APP_SECRET"),
        "broker_id": _secret_value(cfg, "broker_id", "SANDBOX") or "SANDBOX",
        "app_code": _secret_value(cfg, "app_code", "SANDBOX") or "SANDBOX",
        "derivatives_account": _secret_value(cfg, "derivatives_account") or _secret_value(secrets, "SETTRADE_DERIVATIVES_ACCOUNT"),
    }


def _clean(value: Any) -> Any:
    """Convert SDK responses into JSON-safe structures without leaking secrets."""
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
            return {str(k): _clean(v) for k, v in vars(value).items() if not str(k).startswith("_")}
        except Exception:
            pass
    return str(value)


def _unwrap(response: Any) -> Any:
    x = _clean(response)
    if isinstance(x, dict) and "data" in x:
        return x["data"]
    return x


def _call_first(obj: Any, names: list[str]) -> tuple[Any, Optional[str]]:
    last = None
    for name in names:
        fn = getattr(obj, name, None)
        if callable(fn):
            try:
                return fn(), None
            except Exception as exc:  # API method exists but failed
                last = f"{type(exc).__name__}: {exc}"
                return None, last
    return None, f"SDK method not found (tried: {', '.join(names)})"


def connect_read_only(secrets: Any) -> Dict[str, Any]:
    """Connect and read derivatives account/portfolio/orders only."""
    cfg = load_config(secrets)
    result: Dict[str, Any] = {
        "configured": False,
        "connected": False,
        "environment": "SANDBOX" if cfg["broker_id"] == "SANDBOX" or cfg["app_code"] == "SANDBOX" else "UNKNOWN",
        "account": cfg["derivatives_account"],
        "account_info": None,
        "portfolio": None,
        "orders": None,
        "errors": [],
    }

    missing = [k for k in ("app_id", "app_secret", "derivatives_account") if not cfg[k]]
    if missing:
        result["errors"].append("Missing Streamlit secret(s): " + ", ".join(missing))
        return result
    result["configured"] = True

    try:
        from settrade.openapi import Investor
    except Exception as exc:
        result["errors"].append(f"Settrade SDK import failed: {type(exc).__name__}: {exc}")
        return result

    try:
        investor = Investor(
            app_id=cfg["app_id"],
            app_secret=cfg["app_secret"],
            broker_id=cfg["broker_id"],
            app_code=cfg["app_code"],
            is_auto_queue=False,
        )
    except TypeError:
        # Older SDK builds may not expose is_auto_queue.
        try:
            investor = Investor(
                app_id=cfg["app_id"],
                app_secret=cfg["app_secret"],
                broker_id=cfg["broker_id"],
                app_code=cfg["app_code"],
            )
        except Exception as exc:
            result["errors"].append(f"Investor initialization failed: {type(exc).__name__}: {exc}")
            return result
    except Exception as exc:
        result["errors"].append(f"Investor initialization failed: {type(exc).__name__}: {exc}")
        return result

    try:
        deriv = investor.Derivatives(account_no=cfg["derivatives_account"])
    except Exception as exc:
        result["errors"].append(f"Derivatives account initialization failed: {type(exc).__name__}: {exc}")
        return result

    account_info, err = _call_first(deriv, ["get_account_info"])
    if err:
        result["errors"].append(f"Account info: {err}")
    else:
        result["account_info"] = _unwrap(account_info)

    portfolio, err = _call_first(deriv, ["get_portfolio"])
    if err:
        result["errors"].append(f"Portfolio: {err}")
    else:
        result["portfolio"] = _unwrap(portfolio)

    orders, err = _call_first(deriv, ["list_orders"])
    if err:
        result["errors"].append(f"Orders: {err}")
    else:
        result["orders"] = _unwrap(orders)

    # Connection is considered healthy if at least the account endpoint returned.
    result["connected"] = result["account_info"] is not None
    return result
