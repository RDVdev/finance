import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import math
import os
import numpy as np

# --- 1. CONFIGURATION & STYLING ---
st.set_page_config(
    page_title="AssetOS Ultra",
    layout="wide",
    page_icon="🦅",
    initial_sidebar_state="expanded"
)

# Custom CSS for "Financial Terminal" Look
st.markdown("""
<style>
    /* Global Background & Font */
    .stApp {
        background-color: #0e1117;
    }
    
    /* Metrics Cards */
    div[data-testid="stMetricValue"] {
        font-size: 24px;
        color: #ffffff;
    }
    
    /* Custom Card Style */
    .css-card {
        border-radius: 10px;
        padding: 20px;
        background-color: #1e2130;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        margin-bottom: 20px;
        border: 1px solid #30334e;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #161925;
    }
    
    /* Success/Error Text */
    .success-text { color: #2ecc71; font-weight: bold; }
    .danger-text { color: #e74c3c; font-weight: bold; }
    .warning-text { color: #f1c40f; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- 2. CONSTANTS & DATA ---
WATCHLIST_FILE = "my_watchlist.csv"
PORTFOLIO_FILE = "my_portfolio.csv"

# NIFTY 100 (Top 100 Indian Companies)
NIFTY_100 = [
    'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'ICICIBANK.NS', 'INFY.NS', 'BHARTIARTL.NS', 'ITC.NS', 'SBIN.NS', 'LICI.NS', 'HINDUNILVR.NS',
    'LT.NS', 'BAJFINANCE.NS', 'HCLTECH.NS', 'MARUTI.NS', 'SUNPHARMA.NS', 'TITAN.NS', 'ULTRACEMCO.NS', 'TATAMOTORS.NS', 'ASIANPAINT.NS', 'AXISBANK.NS',
    'NTPC.NS', 'POWERGRID.NS', 'M&M.NS', 'ONGC.NS', 'WIPRO.NS', 'ADANIENT.NS', 'JSWSTEEL.NS', 'COALINDIA.NS', 'TATASTEEL.NS', 'BAJAJFINSV.NS',
    'DMART.NS', 'ADANIPORTS.NS', 'KOTAKBANK.NS', 'JIOFIN.NS', 'HAL.NS', 'DLF.NS', 'VBL.NS', 'ZOMATO.NS', 'SIEMENS.NS', 'IRFC.NS',
    'TRENT.NS', 'SBILIFE.NS', 'GRASIM.NS', 'PIDILITIND.NS', 'BEL.NS', 'LTIM.NS', 'PFC.NS', 'IOC.NS', 'TECHM.NS', 'HINDALCO.NS',
    'AMBUJACEM.NS', 'INDUSINDBK.NS', 'BANKBARODA.NS', 'GAIL.NS', 'EICHERMOT.NS', 'DIVISLAB.NS', 'BPCL.NS', 'VEDL.NS', 'ABB.NS', 'ADANIPOWER.NS',
    'GODREJCP.NS', 'TATAPOWER.NS', 'HAVELLS.NS', 'INDIGO.NS', 'CIPLA.NS', 'JSWENERGY.NS', 'DABUR.NS', 'SHREECEM.NS', 'MCDOWELL-N.NS', 'TVSMOTOR.NS',
    'DRREDDY.NS', 'BHEL.NS', 'CHOLAFIN.NS', 'APOLLOHOSP.NS', 'MANKIND.NS', 'NHPC.NS', 'PNB.NS', 'CUMMINSIND.NS', 'BOSCHLTD.NS', 'NAUKRI.NS',
    'ICICIPRULI.NS', 'MUTHOOTFIN.NS', 'HEROMOTOCO.NS', 'TORNTPOWER.NS', 'JINDALSTEL.NS', 'BRITANNIA.NS', 'CGPOWER.NS', 'HDFCLIFE.NS', 'CANBK.NS', 'AUBANK.NS',
    'UNIONBANK.NS', 'IDFCFIRSTB.NS', 'TATAELXSI.NS', 'POLYCAB.NS', 'MRF.NS', 'MARICO.NS', 'SRF.NS', 'ASHOKLEY.NS', 'PIIND.NS', 'PAGEIND.NS'
]

INDICES = {
    "🇮🇳 Nifty 50": "^NSEI",
    "🇮🇳 Sensex": "^BSESN",
    "🇮🇳 Bank Nifty": "^NSEBANK",
    "🇺🇸 S&P 500": "^GSPC",
    "🟡 Gold": "GC=F"
}

# --- 3. HELPER FUNCTIONS ---

def load_csv(filename, columns):
    if os.path.exists(filename):
        return pd.read_csv(filename)
    return pd.DataFrame(columns=columns)

def save_csv(df, filename):
    df.to_csv(filename, index=False)

@st.cache_data(ttl=600)
def fetch_stock_deep_dive(ticker):
    """Fetches detailed data for a single stock."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="6mo")
        
        # Fundamental Data
        data = {
            "Ticker": ticker,
            "Name": info.get('shortName', ticker),
            "Price": info.get('currentPrice', 0.0),
            "Prev Close": info.get('previousClose', 0.0),
            "Market Cap": info.get('marketCap', 0),
            "PE Ratio": info.get('trailingPE', 0.0),
            "Forward PE": info.get('forwardPE', 0.0),
            "PEG Ratio": info.get('pegRatio', 0.0),
            "Price/Book": info.get('priceToBook', 0.0),
            "ROE": info.get('returnOnEquity', 0.0),
            "Debt/Equity": info.get('debtToEquity', 0.0),
            "EPS": info.get('trailingEps', 0.0),
            "Book Value": info.get('bookValue', 0.0),
            "Sector": info.get('sector', 'Unknown'),
            "About": info.get('longBusinessSummary', 'No summary available.')[:400] + "..."
        }
        
        # Intrinsic Value (Graham)
        data['Intrinsic Value'] = 0
        data['Signal'] = "HOLD"
        
        if data['EPS'] > 0 and data['Book Value'] > 0:
            graham = math.sqrt(22.5 * data['EPS'] * data['Book Value'])
            data['Intrinsic Value'] = round(graham, 2)
            
            # Smart Signal Logic
            if data['Price'] < graham:
                data['Signal'] = "BUY"
            elif data['Price'] > graham * 1.5:
                data['Signal'] = "SELL"
        
        return data, hist, stock.news
    except:
        return None, None, None

def plot_interactive_chart(hist, title):
    """Creates a Pro Candlestick chart with Moving Averages."""
    hist['SMA_50'] = hist['Close'].rolling(window=50).mean()
    
    fig = go.Figure()
    
    # Candlestick
    fig.add_trace(go.Candlestick(
        x=hist.index,
        open=hist['Open'], high=hist['High'],
        low=hist['Low'], close=hist['Close'],
        name='Price'
    ))
    
    # Moving Average
    fig.add_trace(go.Scatter(
        x=hist.index, y=hist['SMA_50'],
        mode='lines', name='50 SMA',
        line=dict(color='orange', width=1.5)
    ))
    
    fig.update_layout(
        title=f"{title} - 6 Month Trend",
        template="plotly_dark",
        height=500,
        xaxis_rangeslider_visible=False,
        plot_bgcolor="#1e2130",
        paper_bgcolor="#1e2130",
        font=dict(color="white")
    )
    st.plotly_chart(fig, use_container_width=True)

# --- 4. SIDEBAR NAVIGATION ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3310/3310624.png", width=50) # Placeholder Icon
st.sidebar.title("AssetOS Ultra")
st.sidebar.markdown("---")
menu = st.sidebar.radio(
    "Navigation", 
    ["🏠 Dashboard", "⚡ Quick Scanner", "🔬 Deep Analysis", "💼 Portfolio", "🧮 SIP & Gold"],
)
st.sidebar.info("Data source: Yahoo Finance (Live)")

# --- 5. PAGE: DASHBOARD ---
if menu == "🏠 Dashboard":
    st.title("Market Overview")
    
    # Live Ticker Strip
    cols = st.columns(len(INDICES))
    for i, (name, ticker) in enumerate(INDICES.items()):
        data = yf.Ticker(ticker).history(period="2d")
        if len(data) > 1:
            curr = data['Close'].iloc[-1]
            prev = data['Close'].iloc[-2]
            change = curr - prev
            pct = (change / prev) * 100
            
            color = "normal"
            if pct < 0: color = "inverse"
            
            cols[i].metric(name, f"{int(curr)}", f"{round(pct, 2)}%", delta_color=color)
            
    st.markdown("---")
    
    # Watchlist
    st.subheader("⭐ My Watchlist")
    watchlist = load_csv(WATCHLIST_FILE, ['Ticker'])['Ticker'].tolist()
    
    if watchlist:
        w_data = []
        for t in watchlist:
            info, _, _ = fetch_stock_deep_dive(t)
            if info:
                # Color Coding Signal
                sig_icon = "🟢" if "BUY" in info['Signal'] else ("🔴" if "SELL" in info['Signal'] else "🟡")
                
                w_data.append({
                    "Ticker": t,
                    "Price": info['Price'],
                    "Value": info['Intrinsic Value'],
                    "Signal": f"{sig_icon} {info['Signal']}",
                    "Sector": info['Sector']
                })
        
        st.dataframe(pd.DataFrame(w_data), use_container_width=True, hide_index=True)
    else:
        st.info("Your watchlist is empty. Go to 'Deep Analysis' to add stocks.")

# --- 6. PAGE: SCANNER (Top 100) ---
elif menu == "⚡ Quick Scanner":
    st.title("Market Scanner (Nifty 100)")
    st.markdown("Scan India's Top 100 companies for Undervalued gems.")
    
    if st.button("🚀 Start 100-Stock Scan"):
        results = []
        
        # Progress Bar
        progress_text = "Scanning market... Please wait."
        my_bar = st.progress(0, text=progress_text)
        
        for i, ticker in enumerate(NIFTY_100):
            try:
                # Optimized minimal fetch for speed
                stock = yf.Ticker(ticker)
                info = stock.info
                price = info.get('currentPrice', 0)
                eps = info.get('trailingEps', 0)
                bv = info.get('bookValue', 0)
                
                if eps > 0 and bv > 0:
                    graham = math.sqrt(22.5 * eps * bv)
                    status = "Fair"
                    if price < graham: status = "🟢 BUY"
                    elif price > graham * 1.5: status = "🔴 EXPENSIVE"
                    
                    results.append({
                        "Ticker": ticker,
                        "Price": price,
                        "Intrinsic Value": round(graham, 2),
                        "Status": status,
                        "Sector": info.get('sector', 'N/A')
                    })
            except:
                pass
            
            my_bar.progress((i + 1) / len(NIFTY_100), text=f"Scanning {ticker}...")
            
        my_bar.empty()
        
        # Display Results
        df = pd.DataFrame(results)
        
        # Tabs for Filtering
        tab1, tab2, tab3 = st.tabs(["💎 Undervalued Picks", "🔥 Overvalued", "📋 All Stocks"])
        
        with tab1:
            buys = df[df['Status'].str.contains("BUY")]
            st.success(f"Found {len(buys)} Undervalued Stocks!")
            st.dataframe(buys, use_container_width=True)
            
        with tab2:
            sells = df[df['Status'].str.contains("EXPENSIVE")]
            st.warning(f"Found {len(sells)} Expensive Stocks.")
            st.dataframe(sells, use_container_width=True)
            
        with tab3:
            st.dataframe(df, use_container_width=True)

# --- 7. PAGE: DEEP ANALYSIS ---
elif menu == "🔬 Deep Analysis":
    st.title("Stock Deep Dive")
    
    col_search, col_btn = st.columns([3, 1])
    search_ticker = col_search.text_input("Enter Ticker (e.g., TATAMOTORS.NS)", "TATAMOTORS.NS")
    
    # Add to Watchlist Logic
    watchlist_df = load_csv(WATCHLIST_FILE, ['Ticker'])
    curr_watchlist = watchlist_df['Ticker'].tolist()
    if col_btn.button("➕ Add to Watchlist"):
        if search_ticker not in curr_watchlist:
            curr_watchlist.append(search_ticker)
            save_csv(pd.DataFrame(curr_watchlist, columns=['Ticker']), WATCHLIST_FILE)
            st.toast(f"{search_ticker} added to Watchlist!", icon="✅")

    # Fetch
    info, hist, news = fetch_stock_deep_dive(search_ticker)
    
    if info:
        # Header Badge
        st.markdown(f"## {info['Name']} <span style='font-size: 20px; color: gray;'>({info['Ticker']})</span>", unsafe_allow_html=True)
        
        # Top Metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Current Price", f"₹{info['Price']}")
        m2.metric("Fair Value (Graham)", f"₹{info['Intrinsic Value']}", delta=info['Signal'])
        m3.metric("PE Ratio", round(info['PE Ratio'], 2))
        m4.metric("ROE", f"{round(info['ROE']*100, 2)}%")
        
        st.markdown("---")
        
        # Deep Dive Tabs
        t_chart, t_fund, t_news = st.tabs(["📈 Technical Chart", "📊 Fundamentals", "📰 News"])
        
        with t_chart:
            plot_interactive_chart(hist, search_ticker)
            
        with t_fund:
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("Key Ratios")
                st.write(f"**Market Cap:** ₹{round(info['Market Cap']/10000000)} Cr")
                st.write(f"**Debt to Equity:** {info['Debt/Equity']} (Low is better)")
                st.write(f"**Price to Book:** {info['Price/Book']}")
                st.write(f"**PEG Ratio:** {info['PEG Ratio']} (<1 is undervalued)")
            with c2:
                st.subheader("Business Summary")
                st.info(info['About'])
                
        with t_news:
            if news:
                for n in news[:5]:
                    st.markdown(f"##### [{n['title']}]({n['link']})")
                    st.caption(f"Source: {n['publisher']} | {pd.to_datetime(n['providerPublishTime'], unit='s').strftime('%Y-%m-%d')}")
                    st.divider()

# --- 8. PAGE: PORTFOLIO ---
elif menu == "💼 Portfolio":
    st.title("My Portfolio Tracker")
    
    pf_df = load_csv(PORTFOLIO_FILE, ['Ticker', 'Qty', 'AvgPrice'])
    
    with st.expander("➕ Log New Trade"):
        c1, c2, c3, c4 = st.columns(4)
        p_tic = c1.text_input("Ticker", "INFY.NS")
        p_qty = c2.number_input("Qty", 1)
        p_avg = c3.number_input("Avg Price", 1000.0)
        if c4.button("Save Trade"):
            new_row = pd.DataFrame({'Ticker': [p_tic], 'Qty': [p_qty], 'AvgPrice': [p_avg]})
            pf_df = pd.concat([pf_df, new_row], ignore_index=True)
            save_csv(pf_df, PORTFOLIO_FILE)
            st.rerun()
            
    if not pf_df.empty:
        # Live Calculation
        total_inv = 0
        total_curr = 0
        pf_data = []
        sector_map = {}
        
        for i, row in pf_df.iterrows():
            # Quick fetch just for price
            tick = yf.Ticker(row['Ticker'])
            curr = tick.info.get('currentPrice', row['AvgPrice'])
            sec = tick.info.get('sector', 'Other')
            
            val = curr * row['Qty']
            inv = row['AvgPrice'] * row['Qty']
            
            total_inv += inv
            total_curr += val
            sector_map[sec] = sector_map.get(sec, 0) + val
            
            pf_data.append({
                "Stock": row['Ticker'],
                "Qty": row['Qty'],
                "Avg Price": row['AvgPrice'],
                "LTP": curr,
                "Current Val": round(val, 2),
                "P&L": round(val - inv, 2),
                "P&L %": round((val-inv)/inv*100, 2)
            })
            
        # Summary Cards
        k1, k2, k3 = st.columns(3)
        k1.metric("Total Invested", f"₹{int(total_inv)}")
        k2.metric("Current Value", f"₹{int(total_curr)}")
        pnl = total_curr - total_inv
        k3.metric("Net Profit/Loss", f"₹{int(pnl)}", f"{round(pnl/total_inv*100, 2)}%")
        
        st.markdown("---")
        
        # Visuals
        v1, v2 = st.columns([2, 1])
        with v1:
            st.subheader("Holdings")
            st.dataframe(pd.DataFrame(pf_data), hide_index=True)
        with v2:
            st.subheader("Allocation")
            fig = px.pie(values=list(sector_map.values()), names=list(sector_map.keys()), hole=0.5)
            fig.update_layout(height=350, margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig, use_container_width=True)

# --- 9. PAGE: SIP & GOLD ---
elif menu == "🧮 SIP & Gold":
    st.title("SIP & Commodities Tracker")
    
    # 1. SIP Calculator
    st.subheader("📈 SIP Wealth Projector")
    c1, c2, c3 = st.columns(3)
    inv = c1.number_input("Monthly Investment (₹)", 5000, step=500)
    rate = c2.number_input("Exp. Return (%)", 12.0)
    yrs = c3.number_input("Years", 10)
    
    if st.button("Calculate"):
        months = yrs * 12
        r = rate / 12 / 100
        fv = inv * ((((1 + r) ** months) - 1) / r) * (1 + r)
        invested = inv * months
        gain = fv - invested
        
        st.success(f"Projected Value: ₹{int(fv):,}")
        st.write(f"You Invested: ₹{int(invested):,} | Wealth Gained: ₹{int(gain):,}")
        
        # Chart
        df_chart = pd.DataFrame({"Type": ["Invested", "Gain"], "Amount": [invested, gain]})
        fig = px.bar(df_chart, x="Type", y="Amount", color="Type", title="Wealth Breakdown")
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # 2. Live Commodities
    st.subheader("🟡 Gold & Silver Rates (ETF)")
    commodities = {"Gold Bees": "GOLDBEES.NS", "Silver Bees": "SILVERBEES.NS"}
    
    cc1, cc2 = st.columns(2)
    
    # Gold
    g_tick = yf.Ticker("GOLDBEES.NS")
    g_hist = g_tick.history(period="1mo")
    g_curr = g_hist['Close'].iloc[-1]
    g_prev = g_hist['Close'].iloc[-2]
    cc1.metric("Gold Bees ETF", f"₹{round(g_curr, 2)}", f"{round((g_curr-g_prev)/g_prev*100, 2)}%")
    cc1.line_chart(g_hist['Close'])
    
    # Silver
    s_tick = yf.Ticker("SILVERBEES.NS")
    s_hist = s_tick.history(period="1mo")
    s_curr = s_hist['Close'].iloc[-1]
    s_prev = s_hist['Close'].iloc[-2]
    cc2.metric("Silver Bees ETF", f"₹{round(s_curr, 2)}", f"{round((s_curr-s_prev)/s_prev*100, 2)}%")
    cc2.line_chart(s_hist['Close'])