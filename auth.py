"""
auth.py — EuroEquity Pro
Authentication UI using Supabase via database.py
AManalysis LTD · amanalysis@gmail.com
"""

import streamlit as st
from database import (
    register_user, login_user, get_access, days_left_trial,
    load_portfolios, save_portfolios, update_subscription,
    delete_account, create_stripe_checkout_url, create_tables
)

@st.cache_resource
def _init_db():
    return create_tables()

_init_db()


def render_auth_ui():
    if "user" not in st.session_state:
        st.session_state.user = {}
    user = st.session_state.user

    if user:
        access = get_access(user)
        sub    = user.get("subscription", "trial")
        with st.sidebar:
            st.markdown("---")
            st.markdown(f'<div style="font-size:11px;color:#22d48a;font-weight:700;">👤 {user.get("name","")}</div>', unsafe_allow_html=True)
            st.markdown(f'<div style="font-size:9px;color:#5a6880;">{user.get("email","")}</div>', unsafe_allow_html=True)
            if access == "premium" and sub == "trial":
                st.markdown(f'<div style="font-size:9px;color:#c8982a;margin-top:4px;">⏳ Trial: {days_left_trial(user)} days remaining</div>', unsafe_allow_html=True)
            elif access == "premium":
                st.markdown('<div style="font-size:9px;color:#22d48a;margin-top:4px;">✅ Premium subscriber</div>', unsafe_allow_html=True)
            elif access == "expired":
                st.markdown('<div style="font-size:9px;color:#e84560;margin-top:4px;">⚠️ Trial expired</div>', unsafe_allow_html=True)
            if st.button("🚪 Log out", key="logout_btn"):
                if st.session_state.get("portfolios"):
                    save_portfolios(user["email"], st.session_state.portfolios)
                st.session_state.user = {}
                st.session_state.portfolios = {}
                st.rerun()
        return user

    with st.sidebar:
        st.markdown("---")
        auth_tab = st.radio("", ["Log in","Register"], horizontal=True, label_visibility="collapsed", key="auth_tab")
        if auth_tab == "Log in":
            email_in = st.text_input("Email", key="login_email")
            pass_in  = st.text_input("Password", type="password", key="login_pass")
            if st.button("Log in", key="login_btn"):
                ok, msg, user_data = login_user(email_in, pass_in)
                if ok:
                    st.session_state.user       = user_data
                    st.session_state.portfolios = load_portfolios(user_data["email"])
                    st.rerun()
                else:
                    st.error(msg)
        else:
            name_in  = st.text_input("Full name", key="reg_name")
            email_in = st.text_input("Email", key="reg_email")
            pass_in  = st.text_input("Password (min 8 chars)", type="password", key="reg_pass")
            gdpr_ok  = st.checkbox("I agree to the Terms of Use and Privacy Policy and consent to data processing.", key="gdpr_check")
            sub_ok   = st.checkbox("I agree to a recurring subscription of €4.99/month after the 14-day free trial, automatically renewed unless cancelled.", key="sub_check")
            if st.button("Create free account", key="reg_btn"):
                if not gdpr_ok or not sub_ok:
                    st.error("Please accept the terms to continue.")
                else:
                    ok, msg = register_user(email_in, pass_in, name_in)
                    if ok:
                        _, _, user_data = login_user(email_in, pass_in)
                        st.session_state.user       = user_data
                        st.session_state.portfolios = load_portfolios(user_data["email"])
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
    return {}


def render_upgrade_banner(user: dict):
    access = get_access(user)
    if access == "premium":
        return
    if not user:
        st.warning("🔒 **Create a free account** to access all features. 14-day free trial · No credit card required.")
        return
    st.error("⏳ **Your 14-day free trial has ended.** Subscribe for €4.99/month to continue.")
    checkout_url = create_stripe_checkout_url(user.get("email",""))
    if checkout_url:
        st.markdown(f'<a href="{checkout_url}" target="_blank"><button style="background:#c8982a;color:#07090d;border:none;padding:10px 24px;font-weight:700;border-radius:4px;font-size:14px;cursor:pointer;">Subscribe — €4.99/month</button></a>', unsafe_allow_html=True)
    st.markdown("*Recurring €4.99/month · Cancel anytime*")
