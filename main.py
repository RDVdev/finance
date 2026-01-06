import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import math
import os

# --- PAGE CONFIGURATION (Groww-like Clean UI) ---
st.set_page_config(
    page_title="AssetOS Pro",
    layout="wide",
    page_icon="🚀",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS FOR "CARD" LOOK ---
st.markdown("""
<style>
    .metric-card {
        background-color: #0E1117;
        border: 1px solid #262730;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 10px;
    }
    .stMetric {
        background-color: #0E1117; /* Dark theme compatible */
    }
</style>
""", unsafe_allow_html=True)

# --- CONSTANTS & FILES ---
WATCHLIST_FILE = "my_watchlist.csv"
PORTFOLIO_FILE = "my_portfolio.csv"

POPULAR_STOCKS = [
    'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ITC.NS',
    'SBIN.NS', 'BHARTIARTL.NS', 'HINDUNILVR.NS', 'TATAMOTORS.NS', 'LT.NS',
    'BAJFINANCE.NS', 'MARUTI.NS', 'TITAN.NS', 'ULTRACEMCO.NS', 'ASIANPAINT.NS',
    'ZOMATO.NS', 'PAYTM.NS', 'ADANIENT.NS', 'JIOFIN.NS', 'TATASTEEL.NS'
]

INDICES = {
    "Nifty 50": "^NSEI",
    "Sensex": "^BSESN",
    "Bank Nifty": "^NSEBANK",
    "US Market (S&P 500)": "^GSPC"
}

# --- DATA FUNCTIONS ---

def load_csv(filename, columns):
    if os.path.exists(filename):
        return pd.read_csv(filename)
    return pd.DataFrame(columns=columns)

def save_csv(df, filename):
    df.to_csv(filename, index=False)

@st.cache_data(ttl=300)
def get_stock_info(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="1mo")
        
        # Fundamental Data
        data = {
            "Ticker": ticker,
            "Name": info.get('shortName', ticker),
            "Price": info.get('currentPrice', 0.0),
            "Prev Close": info.get('previousClose', 0.0),
            "Market Cap": info.get('marketCap', 0),
            "PE Ratio": info.get('trailingPE', 0.0),
            "EPS": info.get('trailingEps', 0.0),
            "Book Value": info.get('bookValue', 0.0),
            "Sector": info.get('sector', 'Unknown'),
            "About": info.get('longBusinessSummary', 'No summary available.')[:300] + "..."
        }
        
        # Calculate Change
        data['Change'] = data['Price'] - data['Prev Close']
        data['Change %'] = (data['Change'] / data['Prev Close']) * 100
        
        # Strategy Logic
        data['Intrinsic Value'] = 0
        data['Signal'] = "HOLD"
        
        if data['EPS'] > 0 and data['Book Value'] > 0:
            graham = math.sqrt(22.5 * data['EPS'] * data['Book Value'])
            data['Intrinsic Value'] = round(graham, 2)
            if data['Price'] < graham:
                data['Signal'] = "BUY"
            elif data['Price'] > graham * 1.5:
                data['Signal'] = "SELL"
        
        return data, hist, stock.news
    except:
        return None, None, None

# --- UI COMPONENTS ---

def display_candlestick(hist, title):
    fig = go.Figure(data=[go.Candlestick(
        x=hist.index,
        open=hist['Open'],
        high=hist['High'],
        low=hist['Low'],
        close=hist['Close'],
        name=title
    )])
    fig.update_layout(
        title=f"{title} - 1 Month Trend",
        height=350,
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis_rangeslider_visible=False,
        template="plotly_dark"
    )
    st.plotly_chart(fig, use_container_width=True)

# --- MAIN APP LAYOUT ---

st.sidebar.title("AssetOS 🚀")
menu = st.sidebar.radio("Menu", ["🏠 Dashboard", "🔍 Explore Stocks", "💼 Portfolio", "🧮 SIP Calculator"])

# --- TAB 1: DASHBOARD (MARKET OVERVIEW) ---
if menu == "🏠 Dashboard":
    st.header("Market Overview")
    
    # Live Indices Strip
    cols = st.columns(4)
    for i, (name, ticker) in enumerate(INDICES.items()):
        data = yf.Ticker(ticker).history(period="2d")
        if len(data) > 1:
            curr = data['Close'].iloc[-1]
            prev = data['Close'].iloc[-2]
            change = curr - prev
            pct = (change / prev) * 100
            cols[i].metric(name, f"{int(curr)}", f"{round(pct, 2)}%")
            
    st.markdown("---")
    
    # Watchlist Section
    st.subheader("My Watchlist")
    watchlist = load_csv(WATCHLIST_FILE, ['Ticker'])['Ticker'].tolist()
    
    if watchlist:
        # Create a Summary Table
        summary_data = []
        for t in watchlist:
            info, _, _ = get_stock_info(t)
            if info:
                summary_data.append({
                    "Stock": t,
                    "Price": f"₹{info['Price']}",
                    "Change": f"{round(info['Change %'], 2)}%",
                    "Signal": info['Signal'],
                    "Intrinsic Value": f"₹{info['Intrinsic Value']}"
                })
        
        if summary_data:
            df = pd.DataFrame(summary_data)
            # Custom Coloring for Signals
            st.dataframe(
                df.style.applymap(lambda x: 'color: green' if 'BUY' in str(x) else ('color: red' if 'SELL' in str(x) else ''), subset=['Signal']),
                use_container_width=True
            )
    else:
        st.info("Your watchlist is empty. Go to 'Explore Stocks' to add some.")

# --- TAB 2: EXPLORE (STOCK DETAILS) ---
elif menu == "🔍 Explore Stocks":
    st.title("Explore & Analyze")
    
    # Search Bar
    c1, c2 = st.columns([3, 1])
    search_ticker = c1.text_input("Search Stock (e.g., RELIANCE.NS)", "RELIANCE.NS")
    
    # Quick Add to Watchlist Button
    watchlist_df = load_csv(WATCHLIST_FILE, ['Ticker'])
    curr_watchlist = watchlist_df['Ticker'].tolist()
    
    if c2.button("➕ Add to Watchlist"):
        if search_ticker not in curr_watchlist:
            curr_watchlist.append(search_ticker)
            save_csv(pd.DataFrame(curr_watchlist, columns=['Ticker']), WATCHLIST_FILE)
            st.success(f"Added {search_ticker}!")
    
    # Fetch Data
    info, hist, news = get_stock_info(search_ticker)
    
    if info:
        # Header Metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Price", f"₹{info['Price']}", f"{round(info['Change %'], 2)}%")
        m2.metric("Signal", info['Signal'], f"Target: ₹{info['Intrinsic Value']}")
        m3.metric("PE Ratio", round(info['PE Ratio'], 2))
        m4.metric("Sector", info['Sector'])
        
        # 1. Interactive Chart (Plotly)
        st.subheader("Price Chart")
        display_candlestick(hist, search_ticker)
        
        # 2. Company Info & Stats
        col_left, col_right = st.columns([2, 1])
        with col_left:
            st.subheader("About Company")
            st.write(info['About'])
            
            # News Feed
            st.subheader("📰 Latest News")
            if news:
                for n in news[:3]: # Show top 3 news
                    st.markdown(f"**[{n['title']}]({n['link']})**")
                    st.caption(f"Published by {n['publisher']}")
            else:
                st.write("No recent news found.")
                
        with col_right:
            st.subheader("Key Ratios")
            ratios = {
                "Market Cap": f"₹{round(info['Market Cap']/10000000)} Cr",
                "Book Value": f"₹{round(info['Book Value'], 2)}",
                "EPS": f"₹{round(info['EPS'], 2)}"
            }
            st.table(ratios)

# --- TAB 3: PORTFOLIO (VISUALS) ---
elif menu == "💼 Portfolio":
    st.title("My Portfolio Analysis")
    
    pf_df = load_csv(PORTFOLIO_FILE, ['Ticker', 'Qty', 'AvgPrice'])
    
    # Add Trade Form
    with st.expander("📝 Log a New Trade"):
        c1, c2, c3, c4 = st.columns(4)
        t_tick = c1.text_input("Ticker", "TCS.NS")
        t_qty = c2.number_input("Qty", 1)
        t_avg = c3.number_input("Price", 100.0)
        if c4.button("Save"):
            new_row = pd.DataFrame({'Ticker': [t_tick], 'Qty': [t_qty], 'AvgPrice': [t_avg]})
            pf_df = pd.concat([pf_df, new_row], ignore_index=True)
            save_csv(pf_df, PORTFOLIO_FILE)
            st.rerun()

    if not pf_df.empty:
        # Calculate Live Portfolio
        pf_data = []
        total_inv = 0
        total_curr = 0
        sector_dist = {}
        
        progress = st.progress(0)
        for i, row in pf_df.iterrows():
            info, _, _ = get_stock_info(row['Ticker'])
            if info:
                curr_val = row['Qty'] * info['Price']
                invested = row['Qty'] * row['AvgPrice']
                total_inv += invested
                total_curr += curr_val
                
                # Sector Data for Pie Chart
                sec = info.get('Sector', 'Other')
                sector_dist[sec] = sector_dist.get(sec, 0) + curr_val
                
                pf_data.append({
                    "Stock": row['Ticker'],
                    "Qty": row['Qty'],
                    "Avg": row['AvgPrice'],
                    "LTP": info['Price'],
                    "Current Val": round(curr_val),
                    "P&L": round(curr_val - invested),
                    "P&L %": round((curr_val - invested)/invested * 100, 2)
                })
            progress.progress((i+1)/len(pf_df))
        progress.empty()
        
        # Summary Cards
        total_pnl = total_curr - total_inv
        k1, k2, k3 = st.columns(3)
        k1.metric("Total Invested", f"₹{int(total_inv)}")
        k2.metric("Current Value", f"₹{int(total_curr)}")
        k3.metric("Total Profit/Loss", f"₹{int(total_pnl)}", f"{round((total_pnl/total_inv)*100, 2)}%")
        
        st.markdown("---")
        
        # Visuals: Holdings Table + Pie Chart
        c_table, c_chart = st.columns([2, 1])
        
        with c_table:
            st.subheader("Holdings")
            st.dataframe(pd.DataFrame(pf_data))
            
        with c_chart:
            st.subheader("Sector Allocation")
            if sector_dist:
                fig = px.pie(values=list(sector_dist.values()), names=list(sector_dist.keys()), hole=0.4)
                fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=300)
                st.plotly_chart(fig, use_container_width=True)

# --- TAB 4: CALCULATORS (SIP) ---
elif menu == "🧮 SIP Calculator":
    st.title("SIP Wealth Calculator")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        monthly_inv = st.slider("Monthly Investment (₹)", 500, 100000, 5000, step=500)
        return_rate = st.slider("Expected Return Rate (p.a %)", 5, 30, 12)
        years = st.slider("Time Period (Years)", 1, 40, 10)
    
    # Calculation
    months = years * 12
    monthly_rate = return_rate / 12 / 100
    future_value = monthly_inv * ((((1 + monthly_rate) ** months) - 1) / monthly_rate) * (1 + monthly_rate)
    invested_amount = monthly_inv * months
    wealth_gain = future_value - invested_amount
    
    with col2:
        st.markdown("### Projected Wealth")
        st.metric("Total Value", f"₹{int(future_value):,}")
        st.metric("Invested Amount", f"₹{int(invested_amount):,}")
        st.metric("Wealth Gained", f"₹{int(wealth_gain):,}", delta="Profit")
        
        # Growth Chart
        chart_data = pd.DataFrame({
            "Category": ["Invested", "Wealth Gained"],
            "Amount": [invested_amount, wealth_gain]
        })
        fig = px.pie(chart_data, values="Amount", names="Category", color_discrete_sequence=['#3498db', '#2ecc71'])
        st.plotly_chart(fig, use_container_width=True)