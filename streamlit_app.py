import streamlit as st
import yfinance as yf
import pandas as pd
from groq import Groq
import feedparser

# ----------------------------
# PAGE CONFIG
# ----------------------------

st.set_page_config(page_title="AI Investor Dashboard", layout="wide")

# ----------------------------
# COLORFUL CSS
# ----------------------------

st.markdown("""
<style>

.stApp {
background-color:#f3f4f6;
}

h1 {
color:#2563eb;
}

h2,h3 {
color:#0f766e;
}

/* metric cards */
[data-testid="stMetric"] {
background:white;
padding:14px;
border-radius:12px;
box-shadow:0 4px 10px rgba(0,0,0,0.08);
border-left:6px solid #6366f1;
}

/* metric value */
[data-testid="stMetricValue"] {
color:#2563eb;
font-size:24px;
font-weight:700;
}

/* buttons */
.stButton>button {
background:#6366f1;
color:white;
border-radius:8px;
border:none;
padding:8px 18px;
}

.stButton>button:hover {
background:#4f46e5;
}

/* news cards */
.news-card {
background:white;
padding:12px;
border-radius:10px;
margin-bottom:10px;
border-left:5px solid #10b981;
box-shadow:0 2px 6px rgba(0,0,0,0.05);
}

</style>
""", unsafe_allow_html=True)

# ----------------------------
# HEADER
# ----------------------------

st.title("AI Investor Dashboard")

# ----------------------------
# COMPANY SELECT
# ----------------------------

companies = {
"Reliance":"RELIANCE.NS",
"TCS":"TCS.NS",
"Infosys":"INFY.NS",
"HDFC Bank":"HDFCBANK.NS"
}

company = st.selectbox("Select Company", list(companies.keys()))

ticker = companies[company]

# ----------------------------
# STOCK DATA
# ----------------------------

stock = yf.Ticker(ticker)

data = stock.history(period="max")

price = data["Close"].iloc[-1]

# ----------------------------
# GROWTH FUNCTION
# ----------------------------

def calc_growth(days):

    if len(data) <= days:
        days = len(data)-1

    start = data["Close"].iloc[-days]
    end = data["Close"].iloc[-1]

    return round(((end-start)/start)*100,2)

# ----------------------------
# GROWTH METRICS
# ----------------------------

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

# ----------------------------
# PRICE
# ----------------------------

st.subheader("Current Price")

st.metric("Price",f"₹{price:,.2f}")

# ----------------------------
# NEWS
# ----------------------------

st.subheader("Latest News")

news_url = f"https://news.google.com/rss/search?q={company}+stock"

feed = feedparser.parse(news_url)

news_text=""

for entry in feed.entries[:5]:

    st.markdown(f"""
    <div class="news-card">
    <b>{entry.title}</b><br>
    <a href="{entry.link}" target="_blank">Read full article</a>
    </div>
    """,unsafe_allow_html=True)

    news_text += entry.title + "\n"

# ----------------------------
# AI ANALYSIS
# ----------------------------

st.subheader("AI Analysis")

if st.button("Run AI Analysis"):

    client = Groq(api_key=st.secrets["GROQ_API_KEY"])

    prompt = f"""
    Analyze the stock {company}.

    Current price: {price}

    Growth:
    {growth}

    News:
    {news_text}

    Provide:

    1. Investment score (0-100)
    2. News sentiment
    3. Growth outlook
    4. Expected return next 12 months
    """

    chat = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role":"user","content":prompt}]
    )

    st.write(chat.choices[0].message.content)
