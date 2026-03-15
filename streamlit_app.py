import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import feedparser
import urllib.parse
from datetime import datetime, timedelta
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
from groq import Groq

# ======================
# PAGE CONFIG
# ======================

st.set_page_config(page_title="AI Investment Dashboard", layout="wide")

# ======================
# DARK LIGHT MODE
# ======================

dark = st.sidebar.toggle("🌙 Dark Mode")

if dark:
    st.markdown("""
    <style>
    .stApp{
    background:#0f172a;
    color:white;
    }
    </style>
    """, unsafe_allow_html=True)

# ======================
# GROQ CLIENT
# ======================

try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    client = None

# ======================
# 100+ INDIAN STOCKS
# ======================

STOCKS = {
"Reliance":"RELIANCE.NS",
"TCS":"TCS.NS",
"Infosys":"INFY.NS",
"HDFC Bank":"HDFCBANK.NS",
"ICICI Bank":"ICICIBANK.NS",
"SBI":"SBIN.NS",
"Wipro":"WIPRO.NS",
"L&T":"LT.NS",
"ITC":"ITC.NS",
"HUL":"HINDUNILVR.NS",
"Bharti Airtel":"BHARTIARTL.NS",
"Axis Bank":"AXISBANK.NS",
"Kotak Bank":"KOTAKBANK.NS",
"Adani Enterprises":"ADANIENT.NS",
"Adani Ports":"ADANIPORTS.NS",
"Sun Pharma":"SUNPHARMA.NS",
"Dr Reddy":"DRREDDY.NS",
"Cipla":"CIPLA.NS",
"NTPC":"NTPC.NS",
"ONGC":"ONGC.NS",
"Coal India":"COALINDIA.NS",
"Tata Motors":"TATAMOTORS.NS",
"Tata Steel":"TATASTEEL.NS",
"JSW Steel":"JSWSTEEL.NS",
"Power Grid":"POWERGRID.NS",
"UltraTech Cement":"ULTRACEMCO.NS",
"Asian Paints":"ASIANPAINT.NS",
"Maruti":"MARUTI.NS",
"Hero MotoCorp":"HEROMOTOCO.NS",
"Bajaj Finance":"BAJFINANCE.NS",
"Bajaj Finserv":"BAJAJFINSV.NS",
"Grasim":"GRASIM.NS",
"IndusInd Bank":"INDUSINDBK.NS",
"Tech Mahindra":"TECHM.NS",
"HCL Tech":"HCLTECH.NS"
}

# ======================
# FUNCTIONS
# ======================

def fetch_news(query):

    query = urllib.parse.quote(query)

    url = f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"

    feed = feedparser.parse(url)

    headlines=[]

    cutoff=datetime.now()-timedelta(hours=48)

    for entry in feed.entries:

        if hasattr(entry,"published_parsed"):

            published=datetime(*entry.published_parsed[:6])

            if published>=cutoff:
                headlines.append(entry.title)

    return headlines[:10]


def stock_chart(symbol):

    df = yf.download(symbol, period="6mo")

    df["MA50"]=df["Close"].rolling(50).mean()
    df["MA200"]=df["Close"].rolling(200).mean()

    fig=go.Figure()

    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df["Open"],
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        name="Price"
    ))

    fig.add_trace(go.Scatter(
        x=df.index,
        y=df["MA50"],
        name="MA50"
    ))

    fig.add_trace(go.Scatter(
        x=df.index,
        y=df["MA200"],
        name="MA200"
    ))

    fig.update_layout(
        height=600,
        template="plotly_dark" if dark else "plotly_white"
    )

    st.plotly_chart(fig, use_container_width=True)


def predict_price(symbol):

    df=yf.download(symbol,period="1y")

    df["Days"]=np.arange(len(df))

    X=df[["Days"]]
    y=df["Close"]

    model=LinearRegression()
    model.fit(X,y)

    future=[[len(df)+7]]

    prediction=model.predict(future)

    return round(prediction[0],2)


# ======================
# TITLE
# ======================

st.title("📊 AI Investment Intelligence Platform")

# ======================
# TABS
# ======================

tab1,tab2,tab3,tab4=st.tabs([
"Market Overview",
"Stock Analysis",
"Market News",
"Contact"
])

# ======================
# MARKET OVERVIEW
# ======================

with tab1:

    st.subheader("Market Indices")

    col1,col2,col3=st.columns(3)

    def metric(symbol):

        df=yf.download(symbol,period="2d")

        latest=df["Close"].iloc[-1]
        prev=df["Close"].iloc[-2]

        change=((latest-prev)/prev)*100

        return round(latest,2),round(change,2)

    n,c=metric("^NSEI")
    s,c2=metric("^BSESN")
    b,c3=metric("^NSEBANK")

    col1.metric("NIFTY 50",n,str(c)+"%")
    col2.metric("SENSEX",s,str(c2)+"%")
    col3.metric("BANK NIFTY",b,str(c3)+"%")

# ======================
# STOCK ANALYSIS
# ======================

with tab2:

    st.subheader("Stock Analysis")

    company=st.selectbox("Select Stock",list(STOCKS.keys()))

    symbol=STOCKS[company]

    stock_chart(symbol)

    st.subheader("AI Prediction")

    pred=predict_price(symbol)

    st.metric("Predicted Price (7 Days)",pred)

    df=yf.download(symbol,period="6mo")

    ma50=df["Close"].rolling(50).mean().iloc[-1]
    ma200=df["Close"].rolling(200).mean().iloc[-1]

    if ma50>ma200:
        signal="BUY"
    else:
        signal="SELL"

    st.metric("AI Trading Signal",signal)

# ======================
# MARKET NEWS
# ======================

with tab3:

    st.subheader("Market News")

    news=fetch_news("Indian stock market")

    for n in news:
        st.write("•",n)

    if client:

        st.subheader("AI Market Sentiment")

        prompt=f"""
Analyze these stock market headlines and give:

Market Sentiment
Key Drivers
Short Outlook

Headlines:
{news}
"""

        completion=client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
        {"role":"system","content":"You are a financial analyst"},
        {"role":"user","content":prompt}
        ]
        )

        st.write(completion.choices[0].message.content)

# ======================
# CONTACT
# ======================

with tab4:

    st.subheader("Contact")

    st.write("Ankit Srivastava")
    st.write("Phone: 9616216095")
    st.write("Email: ankit@example.com")
