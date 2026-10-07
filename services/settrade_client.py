import streamlit as st
from settrade.openapi import Investor


def get_investor():
    cfg = st.secrets["settrade"]

    return Investor(
        app_id=cfg["app_id"],
        app_secret=cfg["app_secret"],
        broker_id=cfg["broker_id"],
        app_code=cfg["app_code"],
        is_auto_queue=False,
    )


def get_derivatives_account():
    investor = get_investor()
    account_no = st.secrets["settrade"]["derivatives_account"]

    return investor.Derivatives(account_no)
