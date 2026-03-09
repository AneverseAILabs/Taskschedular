import streamlit as st
import yfinance as yf
import pandas as pd
from groq import Groq
import feedparser

# ------------------------------------
# PAGE CONFIG
# ------------------------------------

st.set_page_config(page_title="AI Investor Dashboard", layout="wide")

# ------------------------------------
# CSS STYLE
# ------------------------------------

st.markdown("""
<style>

.stApp {
background-color:#f6f8fb;
}

h1,h2,h3 {
color:teal;
}

.metric-card {
background:white;
padding:12px;
border-radius:10px;
box-shadow:0 2px 6px rgba(0,0,0,0.05);
}

</style>
""", unsafe_allow_html=True)

st.title("AI Investor Dashboard")

# ------------------------------------
# COMPANY SELECTOR
# ------------------------------------

companies = {
"Reliance":"RELIANCE.NS",
"TCS":"TCS.NS",
"Infosys":"INFY.NS",
"HDFC Bank":"HDFCBANK.NS"
}

company = st.selectbox("Select Company", list(companies.keys()))

ticker = companies[company]

# ------------------------------------
# STOCK DATA
# ------------------------------------

stock = yf.Ticker(ticker)

data = stock.history(period="max")

price = data["Close"].iloc[-1]

# ------------------------------------
# GROWTH FUNCTION
# ------------------------------------

def calc_growth(days):

    if len(data) <= days:
        days = len(data)-1

    start = data["Close"].iloc[-days]
    end = data["Close"].iloc[-1]

    return round(((end-start)/start)*100,2)

# ------------------------------------
# GROWTH METRICS
# ------------------------------------

growth = {
"Overall":calc_growth(len(data)-1),
"15Y":calc_growth(252*15),
"10Y":calc_growth(252*10),
"5Y":calc_growth(252*5),
"3Y":calc_growth(252*3),
"1Y":calc_growth(252),
"6M":calc_growth(126),
"1W":calc_growth(5)
}

st.subheader("Growth Performance")

cols = st.columns(len(growth))

for i,(k,v) in enumerate(growth.items()):
    cols[i].metric(k,f"{v}%")

# ------------------------------------
# PRICE
# ------------------------------------

st.subheader("Current Price")

st.metric("Price",f"₹{price:,.2f}")

# ------------------------------------
# NEWS
# ------------------------------------

st.subheader("Latest News")

news_url = f"https://news.google.com/rss/search?q={company}+stock"

feed = feedparser.parse(news_url)

news_text=""

for entry in feed.entries[:5]:

    st.markdown(f"**{entry.title}**")

    st.write(entry.link)

    news_text += entry.title + "\n"

# ------------------------------------
# AI ANALYSIS
# ------------------------------------

st.subheader("AI Analysis")

if st.button("Run AI Analysis"):

    client = Groq(api_key=st.secrets["GROQ_API_KEY"])

    prompt = f"""
    Analyze the company {company}.

    Current Price: {price}

    Growth:
    {growth}

    News:
    {news_text}

    Provide:
    1. Investment Score (0-100)
    2. News Sentiment
    3. Growth Outlook
    4. Expected return next 12 months
    """

    chat = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role":"user","content":prompt}]
    )

    st.write(chat.choices[0].message.content)
