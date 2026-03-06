import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import feedparser
import ta
import numpy as np
from groq import Groq
from sklearn.linear_model import LinearRegression

st.set_page_config(page_title="AI Investor Dashboard", layout="wide")

st.markdown("<h1 style='color:purple;text-align:center;'>📈 AI Investor Dashboard</h1>", unsafe_allow_html=True)

# Sidebar API key
api_key = st.sidebar.text_input("Groq API Key", type="password")

# Company list
companies = {
"Reliance Industries":"RELIANCE.NS",
"TCS":"TCS.NS",
"Infosys":"INFY.NS",
"HDFC Bank":"HDFCBANK.NS",
"ICICI Bank":"ICICIBANK.NS",
"ITC":"ITC.NS",
"Larsen & Toubro":"LT.NS"
}

company = st.selectbox("Select Company", list(companies.keys()))

ticker = companies[company]

stock = yf.Ticker(ticker)

data = stock.history(period="6mo")

# --------------------------------------------------
# Stock Chart
# --------------------------------------------------

st.subheader("📈 Stock Chart")

fig = go.Figure()

fig.add_trace(go.Candlestick(
    x=data.index,
    open=data["Open"],
    high=data["High"],
    low=data["Low"],
    close=data["Close"]
))

fig.update_layout(height=500)

st.plotly_chart(fig, use_container_width=True)

# --------------------------------------------------
# Technical Indicators
# --------------------------------------------------

data["SMA50"] = ta.trend.sma_indicator(data["Close"], window=50)

data["RSI"] = ta.momentum.rsi(data["Close"], window=14)

data["MACD"] = ta.trend.macd(data["Close"])

st.subheader("📉 Technical Indicators")

col1,col2,col3 = st.columns(3)

col1.metric("RSI", round(data["RSI"].iloc[-1],2))

col2.metric("MACD", round(data["MACD"].iloc[-1],2))

col3.metric("SMA50", round(data["SMA50"].iloc[-1],2))

st.line_chart(data[["Close","SMA50"]])

# --------------------------------------------------
# AI Price Prediction
# --------------------------------------------------

data["Day"] = np.arange(len(data))

X = data[["Day"]]
y = data["Close"]

model = LinearRegression()

model.fit(X,y)

future = np.array([[len(data)+1]])

prediction = model.predict(future)

st.subheader("🧠 AI Price Prediction")

st.success(f"Predicted Next Price: ₹{round(prediction[0],2)}")

# --------------------------------------------------
# News
# --------------------------------------------------

st.subheader("📰 Latest News")

import feedparser
import urllib.parse

st.subheader("📰 Latest News")

query = urllib.parse.quote(company + " stock")

news_url = f"https://news.google.com/rss/search?q={query}"

feed = feedparser.parse(news_url)

if feed.entries:
    for entry in feed.entries[:5]:
        st.markdown(f"**{entry.title}**")
        st.write(entry.link)
else:
    st.write("No news found.")
# --------------------------------------------------
# Investor Recommendation
# --------------------------------------------------

st.subheader("🎯 Investor Type Recommendation")

investor = st.selectbox(
"Select Investor Profile",
["Short Term Trader","Swing Trader","Long Term Investor"]
)

if investor == "Short Term Trader":

    st.info("Use RSI & MACD for quick trades")

elif investor == "Swing Trader":

    st.info("Watch trend and SMA crossovers")

else:

    st.info("Focus on fundamentals and growth")

# --------------------------------------------------
# AI Analysis
# --------------------------------------------------

st.subheader("🤖 AI Stock Analysis")

if st.button("Generate AI Insight"):

    if api_key:

        client = Groq(api_key=api_key)

        prompt = f"""
        Analyze the stock {company}.

        RSI: {data["RSI"].iloc[-1]}
        MACD: {data["MACD"].iloc[-1]}
        SMA50: {data["SMA50"].iloc[-1]}
        Predicted Price: {prediction[0]}

        Provide:
        - company outlook
        - risks
        - recommendation (Buy/Hold/Sell)
        """

        chat = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role":"user","content":prompt}]
        )

        result = chat.choices[0].message.content

        st.write(result)

    else:

        st.warning("Enter Groq API key")
