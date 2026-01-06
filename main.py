import streamlit as st
import yfinance as yf
import pandas as pd
import math
import os

# --- APP CONFIGURATION ---
st.set_page_config(page_title="AssetOS - Smart Investment Dashboard", layout="wide", page_icon="📈")

# --- FILE CONSTANTS ---
WATCHLIST_FILE = "my_watchlist.csv"
PORTFOLIO_FILE = "my_portfolio.csv"

# --- EXPANDED STOCK UNIVERSE (Top 30 Indian Stocks) ---
POPULAR_STOCKS = [
    'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'ICICIBANK.NS', 'INFY.NS',
    'BHARTIARTL.NS', 'ITC.NS', 'SBIN.NS', 'LICI.NS', 'HINDUNILVR.NS',
    'LT.NS', 'BAJFINANCE.NS', 'HCLTECH.NS', 'MARUTI.NS', 'SUNPHARMA.NS',
    'TITAN.NS', 'ULTRACEMCO.NS', 'TATAMOTORS.NS', 'ASIANPAINT.NS', 'AXISBANK.NS',
    'NTPC.NS', 'POWERGRID.NS', 'M&M.NS', 'ONGC.NS', 'WIPRO.NS',
    'ADANIENT.NS', 'JSWSTEEL.NS', 'COALINDIA.NS', 'TATASTEEL.NS', 'BAJAJFINSV.NS'
]

# --- SIP & COMMODITY TICKERS (ETFs as proxies) ---
ETF_TICKERS = {
    "Nifty 50 (Equity SIP)": "NIFTYBEES.NS",
    "Nifty Next 50 (Junior)": "JUNIORBEES.NS",
    "Gold (GoldBees)": "GOLDBEES.NS",
    "Silver (SilverBees)": "SILVERBEES.NS",
    "Bank Nifty": "BANKBEES.NS",
    "IT Sector": "ITBEES.NS"
}

# --- DATA FUNCTIONS ---

def load_csv(filename, columns):
    if os.path.exists(filename):
        return pd.read_csv(filename)
    return pd.DataFrame(columns=columns)

def save_csv(df, filename):
    df.to_csv(filename, index=False)

@st.cache_data(ttl=600) # Cache data for 10 mins to speed up app
def fetch_stock_info(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Safe extraction of data with defaults
        data = {
            "Ticker": ticker,
            "Name": info.get('shortName', ticker),
            "Price": info.get('currentPrice', 0.0),
            "Previous Close": info.get('previousClose', 0.0),
            "PE Ratio": info.get('trailingPE', 0.0),
            "EPS": info.get('trailingEps', 0.0),
            "Book Value": info.get('bookValue', 0.0),
            "52W High": info.get('fiftyTwoWeekHigh', 0.0),
            "52W Low": info.get('fiftyTwoWeekLow', 0.0),
            "Div Yield (%)": round(info.get('dividendYield', 0) * 100, 2) if info.get('dividendYield') else 0
        }
        
        # Graham Calculation
        data['Intrinsic Value'] = 0
        data['Signal'] = "⚪ NEUTRAL"
        
        if data['EPS'] > 0 and data['Book Value'] > 0:
            graham_num = math.sqrt(22.5 * data['EPS'] * data['Book Value'])
            data['Intrinsic Value'] = round(graham_num, 2)
            
            if data['Price'] < graham_num:
                data['Signal'] = "🟢 BUY (Undervalued)"
            elif data['Price'] > graham_num * 1.5:
                 data['Signal'] = "🔴 SELL (Overvalued)"
            else:
                 data['Signal'] = "🟡 HOLD (Fair)"
                 
        return data
    except Exception as e:
        return None

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("AssetOS 📱")
menu = st.sidebar.radio("Navigate", ["📊 Dashboard", "🔍 Market Scanner", "💰 My Portfolio", "🪙 Gold & SIPs"])

# --- PAGE 1: DASHBOARD & WATCHLIST ---
if menu == "📊 Dashboard":
    st.title("Your Market Watchlist")
    
    # Watchlist Logic
    watchlist_df = load_csv(WATCHLIST_FILE, ['Ticker'])
    current_tickers = watchlist_df['Ticker'].tolist()
    
    # Add/Remove
    c1, c2 = st.columns([3, 1])
    new_ticker = c1.text_input("Add Stock (e.g., ZOMATO.NS)")
    if c2.button("Add"):
        if new_ticker and new_ticker not in current_tickers:
            current_tickers.append(new_ticker)
            save_csv(pd.DataFrame(current_tickers, columns=['Ticker']), WATCHLIST_FILE)
            st.rerun()

    # Display Data
    if current_tickers:
        st.write(f"Tracking {len(current_tickers)} stocks...")
        watchlist_data = []
        progress = st.progress(0)
        
        for i, t in enumerate(current_tickers):
            info = fetch_stock_info(t)
            if info: watchlist_data.append(info)
            progress.progress((i + 1) / len(current_tickers))
        
        progress.empty()
        
        if watchlist_data:
            df_display = pd.DataFrame(watchlist_data)
            
            # Key Metrics Display
            st.dataframe(
                df_display[['Ticker', 'Price', 'Signal', 'Intrinsic Value', 'PE Ratio', 'Div Yield (%)']],
                use_container_width=True,
                hide_index=True
            )
            
            # Quick Delete
            to_del = st.selectbox("Remove Stock:", ["Select..."] + current_tickers)
            if st.button("Delete Selected"):
                if to_del != "Select...":
                    current_tickers.remove(to_del)
                    save_csv(pd.DataFrame(current_tickers, columns=['Ticker']), WATCHLIST_FILE)
                    st.rerun()
    else:
        st.info("Watchlist is empty. Add a stock to get started!")

# --- PAGE 2: MARKET SCANNER ---
elif menu == "🔍 Market Scanner":
    st.title("Deep Value Scanner")
    st.markdown("Scanning Top 30 Indian Companies for Undervalued Opportunities.")
    
    if st.button("🚀 Run Full Scan"):
        scan_results = []
        bar = st.progress(0)
        
        for i, t in enumerate(POPULAR_STOCKS):
            info = fetch_stock_info(t)
            if info: scan_results.append(info)
            bar.progress((i + 1) / len(POPULAR_STOCKS))
            
        bar.empty()
        
        full_df = pd.DataFrame(scan_results)
        
        # Filter for BUY signals
        buys = full_df[full_df['Signal'].str.contains("BUY")]
        
        c1, c2 = st.columns(2)
        with c1:
            st.subheader(f"💎 Found {len(buys)} Undervalued Gems")
            if not buys.empty:
                st.success("These stocks are trading BELOW their Graham Intrinsic Value.")
                st.dataframe(buys[['Ticker', 'Price', 'Intrinsic Value', 'PE Ratio']], hide_index=True)
            else:
                st.warning("No clear 'Undervalued' stocks found in this list. Market might be hot.")
                
        with c2:
            st.subheader("All Scanned Stocks")
            st.dataframe(full_df[['Ticker', 'Price', 'Signal']], height=400)
            
        # Download Feature
        csv = full_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Scan Report", csv, "market_scan.csv", "text/csv")

# --- PAGE 3: PORTFOLIO TRACKER ---
elif menu == "💰 My Portfolio":
    st.title("My Holdings")
    
    # Load Portfolio
    pf_df = load_csv(PORTFOLIO_FILE, ['Ticker', 'Qty', 'AvgPrice'])
    
    # Input Form
    with st.expander("➕ Add New Trade"):
        c1, c2, c3 = st.columns(3)
        p_ticker = c1.text_input("Ticker", "TATASTEEL.NS")
        p_qty = c2.number_input("Quantity", min_value=1, value=10)
        p_price = c3.number_input("Avg Buy Price", min_value=1.0, value=100.0)
        
        if st.button("Save Trade"):
            new_row = pd.DataFrame({'Ticker': [p_ticker], 'Qty': [p_qty], 'AvgPrice': [p_price]})
            pf_df = pd.concat([pf_df, new_row], ignore_index=True)
            save_csv(pf_df, PORTFOLIO_FILE)
            st.success("Trade Added!")
            st.rerun()

    # Calculate Live Value
    if not pf_df.empty:
        live_data = []
        total_invested = 0
        current_value = 0
        
        for index, row in pf_df.iterrows():
            info = fetch_stock_info(row['Ticker'])
            curr_price = info['Price'] if info else 0
            
            invested = row['Qty'] * row['AvgPrice']
            curr_val = row['Qty'] * curr_price
            pnl = curr_val - invested
            pnl_pct = (pnl / invested * 100) if invested > 0 else 0
            
            total_invested += invested
            current_value += curr_val
            
            live_data.append({
                "Ticker": row['Ticker'],
                "Qty": row['Qty'],
                "Buy Price": row['AvgPrice'],
                "CMP": curr_price,
                "Invested": round(invested, 2),
                "Current Val": round(curr_val, 2),
                "P&L": round(pnl, 2),
                "Return %": round(pnl_pct, 2)
            })
            
        # Summary Metrics
        st.markdown("### Portfolio Summary")
        k1, k2, k3 = st.columns(3)
        k1.metric("Total Invested", f"₹{round(total_invested)}")
        k2.metric("Current Value", f"₹{round(current_value)}")
        
        total_pnl = current_value - total_invested
        k3.metric("Total P&L", f"₹{round(total_pnl)}", delta=f"{round((total_pnl/total_invested)*100, 2)}%")
        
        st.dataframe(pd.DataFrame(live_data), use_container_width=True)
        
        if st.button("Clear Portfolio (Reset)"):
            save_csv(pd.DataFrame(columns=['Ticker', 'Qty', 'AvgPrice']), PORTFOLIO_FILE)
            st.rerun()

# --- PAGE 4: GOLD, SILVER & SIPS ---
elif menu == "🪙 Gold & SIPs":
    st.title("Passive Wealth Tracker")
    st.markdown("Track the performance of Gold, Silver, and Market Indices (Best for SIPs).")
    
    col1, col2 = st.columns(2)
    
    # Fetch Data for ETFs
    etf_data = []
    for name, ticker in ETF_TICKERS.items():
        data = fetch_stock_info(ticker)
        if data:
            change = data['Price'] - data['Previous Close']
            pct_change = (change / data['Previous Close']) * 100
            etf_data.append({
                "Asset": name,
                "Ticker": ticker,
                "Price": f"₹{data['Price']}",
                "Change": f"{round(pct_change, 2)}%"
            })

    # Display Cards
    for item in etf_data:
        color = "normal"
        if "-" in item['Change']: color = "inverse" # Red for negative
        
        st.metric(label=item['Asset'], value=item['Price'], delta=item['Change'])
        st.divider()

    st.info("💡 **Tip:** Use 'NIFTYBEES' for equity SIPs and 'GOLDBEES' for digital gold investment directly from your demat account.")