import streamlit as st
import yfinance as yf
import pandas as pd
import feedparser
import urllib.parse
from datetime import datetime, timedelta
from groq import Groq
import ta

# ======================
# PAGE CONFIG
# ======================

st.set_page_config(page_title="AI Investment Dashboard", layout="wide")

# ======================
# UI THEME
# ======================

st.markdown("""
<style>

.stApp{
background:#f3f4f6;
}

h1{
color:seagreen;
}

h2,h3{
color:indigo;
}

.metric-box{
background:white;
padding:15px;
border-radius:10px;
border-left:6px solid gray;
text-align:center;
}

.news-card{
background:white;
padding:10px;
border-radius:8px;
border-left:6px solid indigo;
margin-bottom:8px;
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
    <div class="metric-box">
    <h3>NIFTY 50</h3>
    <h2>{p}</h2>
    <p>{c}%</p>
    </div>
    """,unsafe_allow_html=True)

with col2:

    p,c = metric("^BSESN")

    st.markdown(f"""
    <div class="metric-box">
    <h3>SENSEX</h3>
    <h2>{p}</h2>
    <p>{c}%</p>
    </div>
    """,unsafe_allow_html=True)

with col3:

    p,c = metric("^NSEBANK")

    st.markdown(f"""
    <div class="metric-box">
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

changes={}

for t in tickers:

    close=data["Close"][t]

    change=((close.iloc[-1]-close.iloc[-2])/close.iloc[-2])*100

    changes[t]=round(change,2)

df=pd.DataFrame(list(changes.items()),columns=["Stock","Change %"])

col1,col2=st.columns(2)

with col1:
    st.write("📈 Gainers")
    st.dataframe(df.sort_values("Change %",ascending=False)
    .style.background_gradient(cmap="Greens"))

with col2:
    st.write("📉 Losers")
    st.dataframe(df.sort_values("Change %")
    .style.background_gradient(cmap="Reds"))

# ======================
# SECTOR PERFORMANCE
# ======================

st.subheader("Sector Performance")

sector_data={}

for sector in SECTOR_COMPANIES:

    stocks=SECTOR_COMPANIES[sector][:3]

    change_list=[]

    for s in stocks:

        try:

            df=yf.Ticker(s.replace(" ","")+".NS").history(period="2d")

            latest=df["Close"].iloc[-1]
            prev=df["Close"].iloc[-2]

            change=((latest-prev)/prev)*100

            change_list.append(change)

        except:
            pass

    if change_list:
        sector_data[sector]=round(sum(change_list)/len(change_list),2)

sector_df=pd.DataFrame(list(sector_data.items()),columns=["Sector","Change %"])

st.dataframe(sector_df.style.background_gradient(cmap="Blues"))

# ======================
# NEWS FUNCTION
# ======================

@st.cache_data(ttl=3600)
def fetch_news(company):

    query=urllib.parse.quote(company+" stock")

    url=f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"

    feed=feedparser.parse(url)

    headlines=[]

    cutoff=datetime.now()-timedelta(hours=48)

    for entry in feed.entries:

        if hasattr(entry,"published_parsed"):

            published=datetime(*entry.published_parsed[:6])

            if published>=cutoff:
                headlines.append(entry.title)

    return headlines[:10]

# ======================
# MARKET NEWS
# ======================

st.subheader("Market News")

market_news=fetch_news("Indian stock market")

for n in market_news:

    st.markdown(f"""
    <div class="news-card">
    {n}
    </div>
    """,unsafe_allow_html=True)

# ======================
# AI MARKET SENTIMENT
# ======================

st.subheader("AI Market Sentiment")

if market_news:

    text="\n".join(market_news)

    prompt=f"""
Analyze Indian stock market sentiment.

Return:

Market Sentiment
Key Drivers
Short Outlook
"""

    completion=client.chat.completions.create(

        model="llama-3.1-8b-instant",

        messages=[
            {"role":"system","content":"You are a financial strategist."},
            {"role":"user","content":prompt}
        ]

    )

    st.write(completion.choices[0].message.content)

# ======================
# TECHNICAL INDICATORS
# ======================

def calculate_indicators(df):

    df["RSI"] = ta.momentum.RSIIndicator(df["Close"]).rsi()

    macd = ta.trend.MACD(df["Close"])
    df["MACD"] = macd.macd()
    df["MACD Signal"] = macd.macd_signal()

    bb = ta.volatility.BollingerBands(df["Close"])
    df["BB High"] = bb.bollinger_hband()
    df["BB Low"] = bb.bollinger_lband()

    df["SMA50"] = ta.trend.sma_indicator(df["Close"], window=50)
    df["SMA200"] = ta.trend.sma_indicator(df["Close"], window=200)

    df["EMA20"] = ta.trend.ema_indicator(df["Close"], window=20)

    df["ADX"] = ta.trend.ADXIndicator(df["High"], df["Low"], df["Close"]).adx()

    df["CCI"] = ta.trend.CCIIndicator(df["High"], df["Low"], df["Close"]).cci()

    df["OBV"] = ta.volume.OnBalanceVolumeIndicator(df["Close"], df["Volume"]).on_balance_volume()

    return df

# ======================
# COMPANY ANALYSIS
# ======================

st.subheader("Company Technical Analysis")

sector=st.selectbox("Select Sector",list(SECTOR_COMPANIES.keys()))

company=st.selectbox("Select Company",SECTOR_COMPANIES[sector])

if st.button("Analyze Company"):

    df=yf.Ticker(company.replace(" ","")+".NS").history(period="2y")

    df=calculate_indicators(df)

    latest=df.iloc[-1]

    indicator_data={

        "Indicator":[
        "RSI","MACD","MACD Signal","ADX","CCI",
        "SMA50","SMA200","EMA20","Bollinger High",
        "Bollinger Low","OBV"
        ],

        "Value":[
        round(latest["RSI"],2),
        round(latest["MACD"],2),
        round(latest["MACD Signal"],2),
        round(latest["ADX"],2),
        round(latest["CCI"],2),
        round(latest["SMA50"],2),
        round(latest["SMA200"],2),
        round(latest["EMA20"],2),
        round(latest["BB High"],2),
        round(latest["BB Low"],2),
        round(latest["OBV"],2)
        ]

    }

    indicator_df=pd.DataFrame(indicator_data)

    st.dataframe(indicator_df.style.background_gradient(cmap="viridis"))

    news=fetch_news(company)

    st.subheader("Company News")

    for n in news:
        st.write("•",n)

# ======================
# FOOTER
# ======================

st.markdown("""
<hr>

<div style="text-align:center;color:gray">

<h3 style="color:seagreen">Contact</h3>

Ankit<br>
📞 9616216095

</div>
""", unsafe_allow_html=True)
