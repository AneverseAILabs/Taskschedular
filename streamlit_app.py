import streamlit as st
import feedparser
import urllib.parse
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from groq import Groq

# =========================
# PAGE CONFIG
# =========================

st.set_page_config(page_title="AI Investment Dashboard", layout="wide")
st.markdown("""
<style>

/* APP BACKGROUND */
.stApp{
background-color:#f6f8fb;
}

/* HEADINGS */
h1{
color:#2e8b57;
font-weight:700;
}

h2,h3,h4{
color:#6a5acd;
font-weight:600;
}

/* TEXT */
p,div,span,label{
color:#6b7280;
}

/* CARD STYLE */
.card{
background:white;
padding:22px;
border-radius:14px;
box-shadow:0 4px 14px rgba(0,0,0,0.06);
margin-bottom:20px;
}

/* BUTTON */
.stButton>button{
background:#2e8b57;
color:white;
border-radius:10px;
padding:10px 20px;
border:none;
font-weight:500;
}

.stButton>button:hover{
background:#6a5acd;
color:white;
}

/* METRIC BOX */
[data-testid="stMetric"]{
background:white;
padding:18px;
border-radius:12px;
box-shadow:0 3px 10px rgba(0,0,0,0.05);
border-left:5px solid #2e8b57;
}

/* NEWS CARD */
.news-card{
background:white;
padding:15px;
border-radius:12px;
margin-bottom:12px;
border-left:5px solid #6a5acd;
box-shadow:0 2px 6px rgba(0,0,0,0.05);
}

/* TABLE HEADER */
thead tr th{
background:#f0f9f6;
color:#2e8b57;
font-weight:600;
}

/* SELECTBOX */
div[data-baseweb="select"]{
background:white;
border-radius:10px;
}

/* SEARCH BOX */
input{
border-radius:10px !important;
}

/* CHART COLOR */
[data-testid="stLineChart"]{
background:white;
border-radius:12px;
padding:10px;
}

</style>
""", unsafe_allow_html=True)
# =========================
# GROQ CLIENT
# =========================

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# =========================
# COMPANY DATA
# =========================

SECTOR_COMPANIES = {

"Technology":["TCS","Infosys","Wipro","HCLTech","Tech Mahindra","LTIMindtree","Mphasis","Coforge","Persistent Systems","Oracle Financial"],

"Banking":["HDFC Bank","ICICI Bank","SBI","Axis Bank","Kotak Bank","IndusInd Bank","Bank of Baroda","PNB","Canara Bank","Union Bank"],

"Energy":["Reliance Industries","ONGC","NTPC","Power Grid","Adani Green","Adani Power","Coal India","IOC","BPCL","GAIL"],

"Pharma":["Sun Pharma","Dr Reddy","Cipla","Divis Labs","Biocon","Lupin","Aurobindo Pharma","Torrent Pharma","Alkem Labs","Zydus"],

"Automobile":["Maruti Suzuki","Tata Motors","Mahindra","Bajaj Auto","Hero MotoCorp","Eicher Motors","TVS Motor","Ashok Leyland","Bharat Forge","Motherson"],

"FMCG":["HUL","ITC","Nestle India","Britannia","Dabur","Marico","Tata Consumer","Godrej Consumer","Colgate","Emami"],

"Metals":["Tata Steel","JSW Steel","Hindalco","Vedanta","NMDC","SAIL","Jindal Steel","Hindustan Zinc","NALCO","APL Apollo"]
}

# =========================
# UI
# =========================

st.title("📊 AI Investment Intelligence Dashboard")

col1, col2 = st.columns([3,1])

with col1:
    sector = st.selectbox("Select Sector", list(SECTOR_COMPANIES.keys()))

with col2:
    search = st.text_input("Search Company")

companies = SECTOR_COMPANIES[sector]

if search:
    companies = [c for c in companies if search.lower() in c.lower()]

selected = st.multiselect(
    "Select Companies",
    companies,
    default=companies[:3]
)

# =========================
# FETCH NEWS
# =========================

@st.cache_data(ttl=3600)
def fetch_news(company):

    query = urllib.parse.quote(company + " stock")
    url = f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"

    feed = feedparser.parse(url)

    headlines = []
    cutoff = datetime.now() - timedelta(hours=48)

    for entry in feed.entries:

        if hasattr(entry,"published_parsed") and entry.published_parsed:

            published = datetime(*entry.published_parsed[:6])

            if published >= cutoff:
                headlines.append(entry.title)

    return headlines[:10]

# =========================
# STOCK DATA
# =========================

@st.cache_data(ttl=3600)
def get_stock(company):

    try:
        ticker = yf.Ticker(company.replace(" ","")+".NS")
        df = ticker.history(period="6mo")
        return df
    except:
        return None

# =========================
# GROQ AI ANALYSIS
# =========================

def ai_analysis(company,news):

    text = "\n".join(news)

    prompt = f"""
Analyze these headlines for {company}.

Return structured output:

Sentiment
Growth Signals
Risk Signals
Investment Summary
Confidence Score (1-10)

Headlines:
{text}
"""

    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role":"system","content":"You are a professional stock market analyst."},
            {"role":"user","content":prompt}
        ],
        temperature=0.3
    )

    return completion.choices[0].message.content

# =========================
# ANALYZE
# =========================

if st.button("🚀 Analyze Companies"):

    for company in selected:

        st.markdown("---")
        st.header(company)

        col1,col2 = st.columns([2,1])

        # STOCK CHART
        with col1:

            df = get_stock(company)

            if df is not None and not df.empty:
                st.line_chart(df["Close"])
            else:
                st.write("Stock data unavailable")

        # PRICE METRIC
        with col2:

            if df is not None and not df.empty:

                latest = df["Close"].iloc[-1]
                prev = df["Close"].iloc[-2]

                change = ((latest-prev)/prev)*100

                st.metric("Price", round(latest,2), str(round(change,2))+"%")

        # NEWS
        st.subheader("Latest News")

        news = fetch_news(company)

        if not news:
            st.write("No recent news")
            continue

        for n in news:
            st.write("•", n)

        # AI ANALYSIS
        with st.spinner("AI analyzing investment signals..."):

            insight = ai_analysis(company,news)

        st.subheader("AI Investment Insight")

        st.write(insight)
st.markdown("""
<hr>

<div style="text-align:center;color:gray">

<h3 style="color:teal">Contact</h3>

Ankit<br>
📞 9616216095

</div>
