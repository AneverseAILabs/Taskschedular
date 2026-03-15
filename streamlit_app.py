import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import feedparser
import urllib.parse
from datetime import datetime, timedelta
from groq import Groq
import ta

# =====================
# PAGE CONFIG
# =====================

st.set_page_config(page_title="AI Investment Dashboard", layout="wide")

# =====================
# CSS THEME
# =====================

st.markdown("""
<style>

.stApp{
background:#f4f6fb;
font-family:Arial;
}

h1,h2,h3,h4{
color:gray;
}

.metric-box{
background:white;
padding:20px;
border-radius:14px;
border-left:6px solid seagreen;
text-align:center;
box-shadow:0 6px 20px rgba(0,0,0,0.06);
}

.news-card{
background:white;
padding:14px;
border-radius:12px;
border-left:5px solid indigo;
margin-bottom:10px;
box-shadow:0 6px 18px rgba(0,0,0,0.06);
}

.stButton>button{
background:indigo;
color:white;
border-radius:8px;
padding:8px 22px;
}

.stButton>button:hover{
background:seagreen;
}

</style>
""", unsafe_allow_html=True)

# =====================
# GROQ CLIENT
# =====================

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# =====================
# SIDEBAR
# =====================

with st.sidebar:

    st.title("AI Investment")

    page = st.radio(
        "Navigation",
        [
            "Market Overview",
            "Sector Performance",
            "Company Analysis",
            "Market News"
        ]
    )

# =====================
# MARKET OVERVIEW
# =====================

def metric(symbol):

    df = yf.Ticker(symbol).history(period="5d")

    latest = df["Close"].iloc[-1]
    prev = df["Close"].iloc[-2]

    change = ((latest-prev)/prev)*100

    return round(latest,2), round(change,2)


if page == "Market Overview":

    st.title("Market Overview")

    col1,col2,col3 = st.columns(3)

    p,c = metric("^NSEI")
    p2,c2 = metric("^BSESN")
    p3,c3 = metric("^NSEBANK")

    with col1:
        st.markdown(f"""
        <div class="metric-box">
        <h3>NIFTY 50</h3>
        <h2>{p}</h2>
        <p>{c}%</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-box">
        <h3>SENSEX</h3>
        <h2>{p2}</h2>
        <p>{c2}%</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-box">
        <h3>BANK NIFTY</h3>
        <h2>{p3}</h2>
        <p>{c3}%</p>
        </div>
        """, unsafe_allow_html=True)

    st.subheader("Index Trend")

    index_data = yf.download(
        ["^NSEI","^BSESN"],
        period="6mo",
        progress=False
    )["Close"]

    df = index_data.reset_index().melt(
        id_vars="Date",
        var_name="Index",
        value_name="Price"
    )

    fig = px.line(
        df,
        x="Date",
        y="Price",
        color="Index"
    )

    st.plotly_chart(fig,use_container_width=True)

# =====================
# SECTOR PERFORMANCE
# =====================

SECTOR_COMPANIES = {

"Technology":["TCS","Infosys","Wipro"],

"Banking":["HDFC Bank","ICICI Bank","SBI"],

"Energy":["Reliance Industries","ONGC","NTPC"],

"Pharma":["Sun Pharma","Dr Reddy","Cipla"],

"Automobile":["Maruti Suzuki","Tata Motors","Mahindra"]

}

if page == "Sector Performance":

    st.title("Sector Performance")

    sector_data={}

    for sector in SECTOR_COMPANIES:

        stocks=SECTOR_COMPANIES[sector]

        changes=[]

        for s in stocks:

            df=yf.Ticker(s.replace(" ","")+".NS").history(period="2d")

            latest=df["Close"].iloc[-1]
            prev=df["Close"].iloc[-2]

            change=((latest-prev)/prev)*100

            changes.append(change)

        sector_data[sector]=round(sum(changes)/len(changes),2)

    sector_df=pd.DataFrame(
        list(sector_data.items()),
        columns=["Sector","Change %"]
    )

    st.dataframe(sector_df)

    fig = px.bar(
        sector_df,
        x="Sector",
        y="Change %",
        color="Change %",
        color_continuous_scale="Viridis"
    )

    st.plotly_chart(fig,use_container_width=True)

# =====================
# COMPANY ANALYSIS
# =====================

if page == "Company Analysis":

    st.title("Company Technical Analysis")

    sector = st.selectbox(
        "Select Sector",
        list(SECTOR_COMPANIES.keys())
    )

    company = st.selectbox(
        "Select Company",
        SECTOR_COMPANIES[sector]
    )

    df = yf.Ticker(
        company.replace(" ","")+".NS"
    ).history(period="2y")

    df["RSI"]=ta.momentum.RSIIndicator(df["Close"]).rsi()

    df["SMA50"]=ta.trend.sma_indicator(df["Close"],50)

    st.subheader("Price Trend")

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df.index,
        y=df["Close"],
        name="Price",
        line=dict(color="seagreen")
    ))

    fig.add_trace(go.Scatter(
        x=df.index,
        y=df["SMA50"],
        name="SMA50",
        line=dict(color="indigo")
    ))

    st.plotly_chart(fig,use_container_width=True)

    st.subheader("RSI Indicator")

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df.index,
        y=df["RSI"],
        name="RSI",
        line=dict(color="gray")
    ))

    fig.add_hline(y=70)
    fig.add_hline(y=30)

    st.plotly_chart(fig,use_container_width=True)

    latest=df.iloc[-1]

    indicators=pd.DataFrame({

        "Indicator":[
            "RSI",
            "SMA50"
        ],

        "Value":[
            round(latest["RSI"],2),
            round(latest["SMA50"],2)
        ]

    })

    st.subheader("Indicator Data")

    st.dataframe(indicators)

# =====================
# NEWS
# =====================

def fetch_news(topic):

    query=urllib.parse.quote(topic)

    url=f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"

    feed=feedparser.parse(url)

    return [e.title for e in feed.entries[:10]]

if page == "Market News":

    st.title("Market News")

    news=fetch_news("Indian stock market")

    for n in news:

        st.markdown(f"""
        <div class="news-card">
        {n}
        </div>
        """, unsafe_allow_html=True)

    st.subheader("AI Market Sentiment")

    text="\n".join(news)

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

# =====================
# FOOTER
# =====================

st.markdown("""

---

<center style="color:gray">

AI Investment Intelligence Dashboard

Built with Python • Streamlit • AI

</center>

""", unsafe_allow_html=True)
