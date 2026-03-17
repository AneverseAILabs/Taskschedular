import streamlit as st
import yfinance as yf
import pandas as pd
import feedparser
import urllib.parse
import numpy as np
from datetime import datetime, timedelta
from groq import Groq

# ======================
# PAGE CONFIG
# ======================

st.set_page_config(page_title="AI Investment Dashboard", layout="wide")

# ======================
# UI THEME
# ======================

st.markdown("""
<style>
.stApp{background:#f6f9fb;}
h1{color:#2e8b57;}
h2,h3,h4{color:#6a5acd;}
p,div,span,label{color:#6b7280;}
.stButton>button{
background:#2e8b57;
color:white;
border-radius:10px;
padding:8px 20px;
border:none;
}
.stButton>button:hover{background:#6a5acd;}
.news-card{
background:white;
padding:12px;
border-radius:10px;
border-left:5px solid #6a5acd;
margin-bottom:10px;
box-shadow:0 2px 6px rgba(0,0,0,0.05);
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
# AI FUNCTION
# ======================

def run_ai(prompt):

    if client is None:
        return "neutral"

    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role":"system","content":"Reply only with positive, negative or neutral."},
                {"role":"user","content":prompt}
            ]
        )
        return completion.choices[0].message.content.lower()

    except:
        return "neutral"

# ======================
# SECTOR DATA
# ======================

SECTOR_COMPANIES = {
"Technology":["TCS","Infosys","Wipro","HCLTech","Tech Mahindra"],
"Banking":["HDFC Bank","ICICI Bank","SBI","Axis Bank","Kotak Bank"],
"Energy":["Reliance Industries","ONGC","NTPC","Power Grid","Coal India"],
"Pharma":["Sun Pharma","Dr Reddy","Cipla","Divis Labs","Biocon"],
"Automobile":["Maruti Suzuki","Tata Motors","Mahindra","Bajaj Auto","Hero MotoCorp"],
"FMCG":["HUL","ITC","Nestle India","Britannia","Dabur"],
"Metals":["Tata Steel","JSW Steel","Hindalco","Vedanta","SAIL"]
}

# ======================
# TITLE
# ======================

st.title("📊 AI Investment Intelligence Dashboard")

# ======================
# MARKET OVERVIEW
# ======================

st.subheader("📊 Market Overview")

col1,col2,col3 = st.columns(3)

def market_metric(symbol):
    try:
        df = yf.Ticker(symbol).history(period="5d")
        latest = df["Close"].iloc[-1]
        prev = df["Close"].iloc[-2]
        change = ((latest-prev)/prev)*100
        return round(latest,2), round(change,2)
    except:
        return None,None

with col1:
    p,c = market_metric("^NSEI")
    st.metric("NIFTY 50", p, str(c)+"%")

with col2:
    p,c = market_metric("^BSESN")
    st.metric("SENSEX", p, str(c)+"%")

with col3:
    p,c = market_metric("^NSEBANK")
    st.metric("BANK NIFTY", p, str(c)+"%")

# ======================
# NEWS FUNCTION
# ======================

@st.cache_data(ttl=3600)
def fetch_news(company):

    query = urllib.parse.quote(company+" stock")
    url = f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"
    feed = feedparser.parse(url)

    headlines = []
    cutoff = datetime.now()-timedelta(hours=48)

    for entry in feed.entries:
        if hasattr(entry,"published_parsed"):
            published = datetime(*entry.published_parsed[:6])
            if published >= cutoff:
                headlines.append(entry.title)

    return headlines[:10]

# ======================
# MARKET NEWS
# ======================

st.subheader("📰 Market News")

market_news = fetch_news("Indian stock market")

for n in market_news:
    st.markdown(f"<div class='news-card'>{n}</div>", unsafe_allow_html=True)

# ======================
# COMPANY ANALYSIS
# ======================

st.subheader("📈 Company Analysis")

sector = st.selectbox("Select Sector", list(SECTOR_COMPANIES.keys()))
company = st.selectbox("Select Company", SECTOR_COMPANIES[sector])

if st.button("Analyze Company"):

    ticker = company.replace(" ","")+".NS"
    df = yf.Ticker(ticker).history(period="1y")

    if not df.empty:
        st.line_chart(df["Close"])

    news = fetch_news(company)

    for n in news:
        st.write("•", n)

# ======================
# SMART STOCK SCANNER
# ======================

st.subheader("🚀 Smart Stock Scanner")

scan_sector = st.selectbox("Scan Sector", list(SECTOR_COMPANIES.keys()), key="scan")

def get_signal(company):

    try:
        ticker = company.replace(" ","")+".NS"
        df = yf.Ticker(ticker).history(period="10d")

        trend = df["Close"].pct_change().mean()
        volume_spike = df["Volume"].iloc[-1] > df["Volume"].mean()

        news = fetch_news(company)
        sentiment = run_ai("\n".join(news))

        score = 0

        if "positive" in sentiment:
            score += 2
        elif "negative" in sentiment:
            score -= 2

        if trend > 0:
            score += 2
        else:
            score -= 1

        if volume_spike:
            score += 1

        return score

    except:
        return 0

if st.button("Run Scan"):

    top, neutral, avoid = [], [], []

    for comp in SECTOR_COMPANIES[scan_sector]:

        score = get_signal(comp)

        if score >= 4:
            top.append(comp)
        elif score <= 0:
            avoid.append(comp)
        else:
            neutral.append(comp)

    col1,col2,col3 = st.columns(3)

    with col1:
        st.markdown("### 🟢 Top Performers")
        for s in top:
            st.success(s)

    with col2:
        st.markdown("### 🟡 Neutral")
        for s in neutral:
            st.warning(s)

    with col3:
        st.markdown("### 🔴 Avoid")
        for s in avoid:
            st.error(s)

# ======================
# CONTACT
# ======================

st.markdown("""
<hr>
<div style="text-align:center;color:gray">
<h3 style="color:teal">Contact</h3>
Ankit<br>
📞 9616216095
</div>
""", unsafe_allow_html=True)
