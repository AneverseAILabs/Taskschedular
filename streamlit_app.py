
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
# MULTICOLOR THEME
# ======================

st.markdown("""
<style>

.stApp{
background:#f8fafc;
}

/* Headings */

h1{color:#4f46e5;}
h2{color:#6b7280;}
h3{color:#374151;}

/* Metric Cards */

.metric-green{
background:white;
padding:15px;
border-radius:10px;
border-left:6px solid seagreen;
box-shadow:0px 4px 12px rgba(0,0,0,0.08);
}

.metric-indigo{
background:white;
padding:15px;
border-radius:10px;
border-left:6px solid indigo;
box-shadow:0px 4px 12px rgba(0,0,0,0.08);
}

.metric-orange{
background:white;
padding:15px;
border-radius:10px;
border-left:6px solid orange;
box-shadow:0px 4px 12px rgba(0,0,0,0.08);
}

/* News Cards */

.news-card{
background:white;
padding:12px;
border-radius:10px;
border-left:5px solid purple;
margin-bottom:10px;
box-shadow:0px 4px 12px rgba(0,0,0,0.08);
}

/* Buttons */

.stButton>button{
background:indigo;
color:white;
border-radius:8px;
padding:8px 20px;
}

.stButton>button:hover{
background:seagreen;
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

"Technology":["TCS","Infosys","Wipro"],

"Banking":["HDFC Bank","ICICI Bank","SBI"],

"Energy":["Reliance Industries","ONGC","NTPC"],

"Pharma":["Sun Pharma","Dr Reddy","Cipla"]

}

# ======================
# FUNCTIONS
# ======================

def metric(symbol):

    try:

        df = yf.Ticker(symbol).history(period="5d")

        latest = df["Close"].iloc[-1]
        prev = df["Close"].iloc[-2]

        change = ((latest-prev)/prev)*100

        return round(latest,2), round(change,2)

    except:
        return "NA","NA"


@st.cache_data(ttl=3600)
def fetch_news(query):

    query = urllib.parse.quote(query)

    url = f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"

    feed = feedparser.parse(url)

    headlines = []

    cutoff = datetime.now()-timedelta(hours=48)

    for entry in feed.entries:

        if hasattr(entry,"published_parsed"):

            published=datetime(*entry.published_parsed[:6])

            if published>=cutoff:
                headlines.append(entry.title)

    return headlines[:10]

# ======================
# TITLE
# ======================

st.title("📊 AI Investment Intelligence Dashboard")

# ======================
# TABS
# ======================

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
"Market Overview",
"Top Gainers",
"Sector Performance",
"Market News",
"Company Analysis",
"Contact"
])

# ======================
# TAB 1 MARKET OVERVIEW
# ======================

with tab1:

    st.subheader("Market Overview")

    col1,col2,col3 = st.columns(3)

    p,c = metric("^NSEI")
    p2,c2 = metric("^BSESN")
    p3,c3 = metric("^NSEBANK")

    with col1:
        st.markdown(f"""
        <div class="metric-green">
        <h3>NIFTY 50</h3>
        <h2>{p}</h2>
        <p>{c}%</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-indigo">
        <h3>SENSEX</h3>
        <h2>{p2}</h2>
        <p>{c2}%</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-orange">
        <h3>BANK NIFTY</h3>
        <h2>{p3}</h2>
        <p>{c3}%</p>
        </div>
        """, unsafe_allow_html=True)

# ======================
# TAB 2 TOP GAINERS
# ======================

with tab2:

    st.subheader("📈 Latest Top Gainers")

    stocks = [
    "RELIANCE.NS","TCS.NS","INFY.NS",
    "HDFCBANK.NS","ICICIBANK.NS",
    "ITC.NS","SBIN.NS"
    ]

    data = yf.download(stocks, period="2d", progress=False)["Close"]

    gainers = []

    for stock in data.columns:

        prev = data[stock].iloc[-2]
        latest = data[stock].iloc[-1]

        change = ((latest-prev)/prev)*100

        gainers.append({
        "Stock":stock.replace(".NS",""),
        "Price":round(latest,2),
        "Change %":round(change,2)
        })

    df = pd.DataFrame(gainers)

    st.dataframe(df.sort_values("Change %",ascending=False))

# ======================
# TAB 3 SECTOR PERFORMANCE
# ======================

with tab3:

    st.subheader("Sector Performance")

    sector_data={}

    for sector in SECTOR_COMPANIES:

        stocks = SECTOR_COMPANIES[sector]

        change_list=[]

        for s in stocks:

            try:

                df = yf.Ticker(s.replace(" ","")+".NS").history(period="2d")

                latest=df["Close"].iloc[-1]
                prev=df["Close"].iloc[-2]

                change=((latest-prev)/prev)*100

                change_list.append(change)

            except:
                pass

        if change_list:
            sector_data[sector]=round(sum(change_list)/len(change_list),2)

    sector_df = pd.DataFrame(list(sector_data.items()),columns=["Sector","Change %"])

    st.dataframe(sector_df)

# ======================
# TAB 4 MARKET NEWS
# ======================

with tab4:

    st.subheader("Market News")

    market_news = fetch_news("Indian stock market")

    for n in market_news:

        st.markdown(f"""
        <div class="news-card">
        {n}
        </div>
        """, unsafe_allow_html=True)

    st.subheader("AI Market Sentiment")

    text = "\n".join(market_news)

    prompt = f"""
Analyze sentiment of these headlines.

Return:

Market Sentiment
Key Drivers
Short Outlook

Headlines:
{text}
"""

    completion = client.chat.completions.create(

        model="llama-3.1-8b-instant",

        messages=[
        {"role":"system","content":"You are a financial strategist."},
        {"role":"user","content":prompt}
        ]
    )

    st.write(completion.choices[0].message.content)

# ======================
# TAB 5 COMPANY ANALYSIS
# ======================

with tab5:

    st.subheader("Company Analysis")

    sector = st.selectbox("Select Sector",list(SECTOR_COMPANIES.keys()))

    company = st.selectbox("Select Company",SECTOR_COMPANIES[sector])

    if st.button("Analyze Company"):

        news = fetch_news(company)

        st.subheader("Company News")

        for n in news:
            st.write("•",n)

        prompt = f"""
Analyze investment outlook for {company}

Return:

Investment Rating
Growth Drivers
Risk Factors
Short Term Outlook
Long Term Outlook
"""

        completion = client.chat.completions.create(

            model="llama-3.1-8b-instant",

            messages=[
            {"role":"system","content":"You are a stock analyst."},
            {"role":"user","content":prompt}
            ]
        )

        st.subheader("🤖 AI Investment Insight")

        st.write(completion.choices[0].message.content)

# ======================
# TAB 6 CONTACT
# ======================

with tab6:

    st.subheader("Contact")

    st.markdown("""

**Ankit Srivastava**

📞 Phone: 9616216095  
📧 Email: ankit@example.com  
💼 LinkedIn: https://linkedin.com  

Feel free to reach out for collaboration or questions regarding the AI Investment Dashboard.

""")

