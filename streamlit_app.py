```python
import streamlit as st
import yfinance as yf
import pandas as pd
import feedparser
import urllib.parse
from datetime import datetime, timedelta
from groq import Groq

# ======================
# PAGE CONFIG
# ======================

st.set_page_config(page_title="AI Investment Intelligence", layout="wide")

# ======================
# UI THEME
# ======================

st.markdown("""
<style>

.stApp{
background:#f7fafc;
}

h1,h2,h3,h4{
color:gray;
}

.stButton>button{
background:indigo;
color:white;
border-radius:8px;
padding:8px 20px;
}

.stButton>button:hover{
background:seagreen;
}

.news-card{
background:white;
padding:12px;
border-radius:10px;
border-left:5px solid indigo;
margin-bottom:10px;
box-shadow:0px 4px 10px rgba(0,0,0,0.08);
}

.metric-card{
background:white;
padding:16px;
border-radius:10px;
border-left:5px solid seagreen;
text-align:center;
box-shadow:0px 4px 10px rgba(0,0,0,0.08);
}

</style>
""", unsafe_allow_html=True)

# ======================
# GROQ CLIENT
# ======================

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

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

st.subheader("Market Overview")

col1,col2,col3 = st.columns(3)

def metric(symbol):

    try:

        df = yf.Ticker(symbol).history(period="5d")

        latest = df["Close"].iloc[-1]
        prev = df["Close"].iloc[-2]

        change = ((latest-prev)/prev)*100

        return round(latest,2), round(change,2)

    except:

        return "NA","NA"

with col1:

    p,c = metric("^NSEI")

    st.markdown(f"""
    <div class="metric-card">
    <h3>NIFTY 50</h3>
    <h2>{p}</h2>
    <p>{c}%</p>
    </div>
    """,unsafe_allow_html=True)

with col2:

    p,c = metric("^BSESN")

    st.markdown(f"""
    <div class="metric-card">
    <h3>SENSEX</h3>
    <h2>{p}</h2>
    <p>{c}%</p>
    </div>
    """,unsafe_allow_html=True)

with col3:

    p,c = metric("^NSEBANK")

    st.markdown(f"""
    <div class="metric-card">
    <h3>BANK NIFTY</h3>
    <h2>{p}</h2>
    <p>{c}%</p>
    </div>
    """,unsafe_allow_html=True)

# ======================
# TOP GAINERS LOSERS
# ======================

st.subheader("Top Gainers & Losers")

tickers = ["RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS"]

data = yf.download(tickers,period="2d",progress=False)

changes = {}

for t in tickers:

    close = data["Close"][t]

    change = ((close.iloc[-1]-close.iloc[-2])/close.iloc[-2])*100

    changes[t] = round(change,2)

df = pd.DataFrame(list(changes.items()),columns=["Stock","Change %"])

col1,col2 = st.columns(2)

with col1:
    st.write("📈 Gainers")
    st.dataframe(df.sort_values("Change %",ascending=False))

with col2:
    st.write("📉 Losers")
    st.dataframe(df.sort_values("Change %"))

# ======================
# SECTOR PERFORMANCE
# ======================

st.subheader("Sector Performance Summary")

sector_data = {}

for sector in SECTOR_COMPANIES:

    stocks = SECTOR_COMPANIES[sector][:3]

    change_list = []

    for s in stocks:

        try:

            df = yf.Ticker(s.replace(" ","")+".NS").history(period="2d")

            latest = df["Close"].iloc[-1]
            prev = df["Close"].iloc[-2]

            change = ((latest-prev)/prev)*100

            change_list.append(change)

        except:
            pass

    if change_list:
        sector_data[sector] = round(sum(change_list)/len(change_list),2)

sector_df = pd.DataFrame(list(sector_data.items()),columns=["Sector","Change %"])

st.dataframe(sector_df)

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

st.subheader("Market News")

market_news = fetch_news("Indian stock market")

for n in market_news:

    st.markdown(f"""
    <div class="news-card">
    {n}
    </div>
    """,unsafe_allow_html=True)

# ======================
# NEWS SENTIMENT MODEL
# ======================

def analyze_news_sentiment(headlines):

    text = "\n".join(headlines)

    prompt = f"""
Analyze sentiment of these news headlines.

Return:

Market Sentiment (Bullish / Neutral / Bearish)
Sentiment Score (-1 to 1)
Confidence (0-100)
Key Reasons

Headlines:
{text}
"""

    completion = client.chat.completions.create(

        model="llama-3.1-8b-instant",

        messages=[
            {"role":"system","content":"You are a financial sentiment analyst."},
            {"role":"user","content":prompt}
        ]
    )

    return completion.choices[0].message.content

st.subheader("🧠 AI Market Sentiment")

sentiment = analyze_news_sentiment(market_news)

st.write(sentiment)

# ======================
# COMPANY ANALYSIS
# ======================

st.subheader("Company Analysis")

sector = st.selectbox("Select Sector",list(SECTOR_COMPANIES.keys()))

companies = SECTOR_COMPANIES[sector]

company = st.selectbox("Select Company",companies)

# ======================
# AI INVESTMENT ENGINE
# ======================

def ai_investment_recommendation(company, news):

    news_text = "\n".join(news)

    prompt = f"""
You are a professional equity analyst.

Analyze the investment potential of this company.

Company: {company}

Recent News:
{news_text}

Return:

Investment Rating (Strong Buy / Buy / Hold / Sell)

Entry Strategy

Growth Drivers

Risk Factors

Short Term Outlook

Long Term Outlook

Confidence Score (0-100)
"""

    completion = client.chat.completions.create(

        model="llama-3.1-8b-instant",

        messages=[
            {"role":"system","content":"You are a senior equity research analyst."},
            {"role":"user","content":prompt}
        ]
    )

    return completion.choices[0].message.content

if st.button("Analyze Company"):

    news = fetch_news(company)

    st.subheader("Company News")

    for n in news:
        st.write("•",n)

    recommendation = ai_investment_recommendation(company, news)

    st.subheader("🤖 AI Investment Recommendation")

    st.write(recommendation)

# ======================
# FOOTER
# ======================

st.markdown("""
<hr>

<div style="text-align:center;color:gray">

This dashboard provides informational insights only.<br>
Not financial advice. Invest at your own risk.

</div>
""", unsafe_allow_html=True)
```
