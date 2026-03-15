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

st.set_page_config(page_title="AI Investment Dashboard", layout="wide")

# ======================
# UI THEME
# ======================

st.markdown("""
<style>

.stApp{
background:#f6f9fb;
}

h1{
color:#2e8b57;
font-weight:700;
}

h2,h3,h4{
color:#6a5acd;
}

p,div,span,label{
color:#6b7280;
}

.stButton>button{
background:#ffff;
color:white;
border-radius:10px;
padding:8px 20px;
border:none;
}

.stButton>button:hover{
background:#6a5acd;
}

.news-card{
background:white;
padding:14px;
border-radius:12px;
border-left:5px solid #6a5acd;
margin-bottom:10px;
box-shadow:0 2px 6px rgba(0,0,0,0.05);
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

st.subheader("📊 Market Overview")

col1,col2,col3 = st.columns(3)

@st.cache_data
def metric(symbol):

    df = yf.Ticker(symbol).history(period="5d")

    if df.empty:
        return None,None

    latest = df["Close"].iloc[-1]
    prev = df["Close"].iloc[-2]

    change = ((latest-prev)/prev)*100

    return round(latest,2), round(change,2)

with col1:
    p,c = metric("^NSEI")
    st.metric("NIFTY 50",p,str(c)+"%")

with col2:
    p,c = metric("^BSESN")
    st.metric("SENSEX",p,str(c)+"%")

with col3:
    p,c = metric("^NSEBANK")
    st.metric("BANK NIFTY",p,str(c)+"%")

# ======================
# TOP GAINERS LOSERS
# ======================



tickers = ["RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS"]

data = yf.download(tickers,period="2d",progress=False)

changes = {}

for t in tickers:

    try:
        close=data["Close"][t]
        change=((close.iloc[-1]-close.iloc[-2])/close.iloc[-2])*100
        changes[t]=round(change,2)
    except:
        pass

df=pd.DataFrame(list(changes.items()),columns=["Stock","Change %"])



# ======================
# SECTOR PERFORMANCE
# ======================

st.subheader("💰 Sector Performance Summary")

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

st.dataframe(sector_df,use_container_width=True)

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

st.subheader("📰 Overall Market News")

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

st.subheader("🧠 AI Market Sentiment")

if market_news:

    text="\n".join(market_news)

    prompt=f"""
Analyze overall Indian stock market sentiment.

Return:
Market Sentiment
Key Drivers
Short Outlook

Headlines:
{text}
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
# COMPANY ANALYSIS
# ======================

st.subheader("📈 Company Analysis")

sector=st.selectbox("Select Sector",list(SECTOR_COMPANIES.keys()))

companies=SECTOR_COMPANIES[sector]

company=st.selectbox("Select Company",companies)

if st.button("Analyze Company"):

    df=yf.Ticker(company.replace(" ","")+".NS").history(period="10y")

    if not df.empty:

        st.line_chart(df["Close"])

    news=fetch_news(company)

    st.subheader("Company News")

    for n in news:
        st.write("•",n)

    text="\n".join(news)

    prompt=f"""
Analyze investment outlook for {company}.

Return:

Sentiment
Growth Signals
Risk Factors
Investment Summary
Confidence Score
"""

    completion=client.chat.completions.create(

        model="llama-3.1-8b-instant",

        messages=[
            {"role":"system","content":"You are a professional stock analyst."},
            {"role":"user","content":prompt}
        ]

    )

    st.subheader("🤖 AI Investment Insight")

    st.write(completion.choices[0].message.content)

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
