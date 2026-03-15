import streamlit as st
import yfinance as yf
import pandas as pd
import feedparser
import urllib.parse
from datetime import datetime, timedelta
from groq import Groq
import plotly.graph_objects as go

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
background:#f7fafc;
}

h1{
color:#2e8b57;
}

h2,h3,h4{
color:#6a5acd;
}

.stButton>button{
background:indigo;
color:white;
border-radius:8px;
padding:8px 20px;
}

.news-card{
background:white;
padding:12px;
border-radius:10px;
border-left:5px solid #6a5acd;
margin-bottom:10px;
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

st.subheader("🚀 Top Gainers & Losers")

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
    st.dataframe(df.sort_values("Change %",ascending=False))

with col2:
    st.write("📉 Losers")
    st.dataframe(df.sort_values("Change %"))

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

st.bar_chart(sector_df.set_index("Sector"))

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
# COMPANY ANALYSIS
# ======================

st.subheader("📈 Company Analysis")

sector=st.selectbox("Select Sector",list(SECTOR_COMPANIES.keys()))

companies=SECTOR_COMPANIES[sector]

company=st.selectbox("Select Company",companies)

duration = st.selectbox(
    "Chart Duration",
    ["1 Month","3 Months","6 Months","1 Year","5 Years","10 Years"]
)

duration_map = {
    "1 Month":"1mo",
    "3 Months":"3mo",
    "6 Months":"6mo",
    "1 Year":"1y",
    "5 Years":"5y",
    "10 Years":"10y"
}

period = duration_map[duration]

if st.button("Analyze Company"):

    with st.spinner("Analyzing company..."):

        df=yf.Ticker(company.replace(" ","")+".NS").history(period=period)

        df["MA50"]=df["Close"].rolling(50).mean()
        df["MA200"]=df["Close"].rolling(200).mean()

        # ===== Plotly Chart =====

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=df.index,
            y=df["Close"],
            mode="lines",
            name="Close Price"
        ))

        fig.add_trace(go.Scatter(
            x=df.index,
            y=df["MA50"],
            mode="lines",
            name="MA50"
        ))

        fig.add_trace(go.Scatter(
            x=df.index,
            y=df["MA200"],
            mode="lines",
            name="MA200"
        ))

        fig.update_layout(

            title=f"{company} Stock Price",

            xaxis=dict(
                title="Date",
                rangeselector=dict(
                    buttons=list([
                        dict(count=1,label="1m",step="month",stepmode="backward"),
                        dict(count=6,label="6m",step="month",stepmode="backward"),
                        dict(count=1,label="1y",step="year",stepmode="backward"),
                        dict(step="all")
                    ])
                ),
                rangeslider=dict(visible=True),
                type="date"
            ),

            yaxis_title="Price (₹)",

            template="plotly_white",

            hovermode="x unified"

        )

        st.plotly_chart(fig,use_container_width=True)

        # ===== Company News =====

        news=fetch_news(company)

        st.subheader("Company News")

        for n in news:
            st.write("•",n)

        # ===== AI Analysis =====

        text="\n".join(news)

        prompt=f"""
Analyze investment outlook for {company}.

Return structured output:

Sentiment
Growth Drivers
Risk Factors
Short Term Outlook
Long Term Outlook
Investment Summary
Confidence Score
"""

        completion=client.chat.completions.create(

            model="llama-3.1-8b-instant",

            messages=[
                {"role":"system","content":"You are a stock analyst."},
                {"role":"user","content":prompt}
            ]

        )

        st.subheader("🤖 AI Investment Insight")

        st.write(completion.choices[0].message.content)

# ======================
# FOOTER
# ======================

st.markdown("""
<hr>

<div style="text-align:center;color:gray">

<h3 style="color:teal">Contact</h3>

Ankit<br>
📞 9616216095

</div>
""", unsafe_allow_html=True)
