# Main Dashboard (Streamlit Version with Multi-Page and Live Data Support) 
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import requests
from bs4 import BeautifulSoup
import os
import gspread
from gspread_dataframe import set_with_dataframe

if __name__ == "__main__":
    main()

# -------- Simple Auth --------
USER_CREDENTIALS = {
    "admin@example.com": "securepassword123"
}

def simple_login():
    st.sidebar.title("🔐 Login")
    email = st.sidebar.text_input("Email")
    password = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Login"):
        if email in USER_CREDENTIALS and USER_CREDENTIALS[email] == password:
            st.session_state["authenticated"] = True
            st.session_state["user_email"] = email
            st.success(f"Welcome, {email}!")
        else:
            st.error("Invalid credentials.")

# -------- Google Sheets Integration (Test Version) --------
def save_crypto_to_gsheet(email, df):
    try:
        gc = gspread.service_account(filename="test_gspread_key.json")  # replace if local
        sheet = gc.open_by_url("https://docs.google.com/spreadsheets/d/1rBO2DUTqDqFXRoenXB1Tk0fxzbNHzXMHHwYBPIIOs-Q/edit?gid=0#gid=0")
        worksheet = sheet.worksheet("CryptoHoldings")

        df = df.copy()
        df.insert(0, "Timestamp", datetime.utcnow().isoformat())
        df.insert(1, "Email", email)

        existing = pd.DataFrame(worksheet.get_all_records())
        combined = pd.concat([existing, df], ignore_index=True)
        worksheet.clear()
        set_with_dataframe(worksheet, combined)
        return True
    except Exception as e:
        st.error(f"GSheet Save Failed: {e}")
        return False

# -------- Wallet Helpers --------
def fetch_algo_balance(address):
    try:
        url = f"https://algoexplorerapi.io/v2/accounts/{address}"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers)
        data = r.json()
        assets = data.get("assets", [])
        return len(assets)
    except:
        return 0

def fetch_eth_contracts(address):
    try:
        key = os.getenv("ETHERSCAN_API_KEY")
        url = f"https://api.etherscan.io/api?module=account&action=tokentx&address={address}&sort=asc&apikey={key}"
        r = requests.get(url)
        data = r.json()
        txs = data.get("result", [])
        return list(set(tx["contractAddress"] for tx in txs))
    except:
        return []

def fetch_xdc_balance(address):
    try:
        if address.startswith("xdc"):
            address = address.replace("xdc", "0x")
        key = os.getenv("XDC_API_KEY")
        url = f"https://api.xdcscan.io/api?module=account&action=tokentx&address={address}&sort=asc&apikey={key}"
        r = requests.get(url)
        data = r.json()
        txs = data.get("result", [])
        return len(set(tx["contractAddress"] for tx in txs))
    except:
        return 0

# -------- Crypto Exposure Tab --------
def page_crypto_exposure():
    st.title("💰 Crypto Exposure Dashboard")

    st.write("Enter wallet addresses for live balance fetch:")
    algo_wallet = st.text_input("Algorand Wallet Address", "")
    eth_wallet = st.text_input("Ethereum Wallet Address", "")
    xdc_wallet = st.text_input("XDC Wallet Address", "")

    st.write("---")

    lofty_tokens = fetch_algo_balance(algo_wallet) if algo_wallet else 0
    eth_contracts = fetch_eth_contracts(eth_wallet) if eth_wallet else []
    realt_tokens = sum('realt' in c.lower() for c in eth_contracts)
    ondo_tokens = sum('ondo' in c.lower() for c in eth_contracts)
    xdc_tokens = fetch_xdc_balance(xdc_wallet) if xdc_wallet else 0

    yield_lofty = st.number_input("Lofty Yield (%)", min_value=0.0, max_value=20.0, value=7.0)
    yield_realt = st.number_input("RealT Yield (%)", min_value=0.0, max_value=20.0, value=10.0)
    yield_ondo = st.number_input("ONDO Yield (%)", min_value=0.0, max_value=20.0, value=5.0)
    yield_xdc = st.number_input("XDC Yield (%)", min_value=0.0, max_value=20.0, value=8.0)

    data = pd.DataFrame({
        "Platform": ["Lofty", "RealT", "ONDO", "XDC"],
        "Blockchain": ["Algorand", "Ethereum", "Ethereum", "XDC"],
        "Tokens Held": [lofty_tokens, realt_tokens, ondo_tokens, xdc_tokens],
        "Yield (%)": [yield_lofty, yield_realt, yield_ondo, yield_xdc]
    })
    data["Annual Yield ($)"] = data["Tokens Held"] * data["Yield (%)"] * 0.01

    st.subheader("Token Holdings with Yield")
    st.dataframe(data)

    st.subheader("Exposure by Blockchain")
    st.bar_chart(data.groupby("Blockchain")["Tokens Held"].sum())

    st.subheader("Estimated Annual Income")
    st.metric("Total Annual Yield", f"${data['Annual Yield ($)'].sum():,.2f}")

    if st.button("Save to Google Sheet"):
        user_email = st.session_state.get("user_email", "demo@guest")
        if save_crypto_to_gsheet(user_email, data):
            st.success("Saved to shared Google Sheet!")
        else:
            st.warning("Could not save. Check credentials or permissions.")

    if st.button("Add to Portfolio as Virtual Holdings"):
        crypto_props = pd.DataFrame({
            "Address": data["Platform"] + " Wallet",
            "Platform": data["Platform"],
            "Property Value ($)": data["Annual Yield ($)"],
            "DCF ($)": data["Annual Yield ($)"],
            "IRR (%)": data["Yield (%)"],
            "Cap Rate (%)": data["Yield (%)"],
            "Score (Good Deal %)": [80]*4
        })
        if "crypto_holdings" not in st.session_state:
            st.session_state["crypto_holdings"] = crypto_props
        else:
            st.session_state["crypto_holdings"] = pd.concat([st.session_state["crypto_holdings"], crypto_props], ignore_index=True)
        st.success("Added to portfolio view!")

# -------- Main Entry Point --------
def main():
    simple_login()
    if st.session_state.get("authenticated"):
        page_crypto_exposure()

if __name__ == "__main__":
    main()
