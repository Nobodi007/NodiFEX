# TFEX Terminal — V5.1 Settrade Sandbox Diagnostic

# TFEX Journal — Settrade Sandbox Read-only

This build keeps the terminal **read-only**. It connects to Settrade Open API only for account/portfolio/orders and never calls place-order or cancel-order.

## Streamlit Secrets

In Streamlit Cloud → Manage app → Settings → Secrets:

```toml
[settrade]
app_id = "YOUR_APPLICATION_ID"
app_secret = "YOUR_APPLICATION_SECRET"
broker_id = "SANDBOX"
app_code = "SANDBOX"
derivatives_account = "Nobody-D"
```

Do **not** commit the secret to GitHub and do not paste it into chat.

## requirements.txt

Uses `settrade-v2==2.2.1`.

## What this build does

- Authentication / Investor initialization
- Derivatives account initialization
- Account info (read-only)
- Portfolio (read-only)
- Orders (read-only)
- On-screen API diagnostic status
- No fake balances, positions, orders or P/L
- No `place_order`, `change_order`, or `cancel_order` code path

If credentials are missing, the shell still loads and clearly reports `TFEX API NOT CONFIGURED`.


## V5.2 SDK note
The `settrade-v2` package imports as `settrade_v2.user`. The connector tries that import first and falls back to the legacy `settrade.openapi` path.
