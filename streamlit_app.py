```python
import streamlit as st
import yfinance as yf
import pandas as pd
import feedparser
import urllib.parse
from datetime import datetime, timedelta
from groq import Groq
import streamlit.components.v1 as components

# ======================
# PAGE CONFIG
# ======================

st.set_page_config(page_title="AI Investment Dashboard", layout="wide")

# ======================
# PROFESSIONAL CSS
# ======================

st.markdown("""
<style>

.stApp{
background:linear-gradient(135deg,#f8fafc,#eef2ff);
}

h1{color:#4f46e5;}
h2{color:#374151;}
h3{color:#6b7280;}

.metric-card{
background:white;
padding:18px;
border-radius:14px;
border-left:6px solid seagreen;
box-shadow:0 6px 18px rgba(0,0,0,0.08);
}

.news-card{
background:white;
padding:14px;
border-radius:14px;
border-left:5px solid purple;
margin-bottom:12px;
box-shadow:0 6px 18px rgba(0,0,0,0.08);
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
# TRADINGVIEW CHART
# ======================

def tradingview_chart(symbol):

    html = f"""
    <div class="tradingview-widget-container">
      <div id="tradingview_chart"></div>

      <script src="https://s3.tradingview.com/tv.js"></script>

      <script>

      new TradingView.widget({{

      "width": "100%",
      "height": 500,
      "symbol": "{symbol}",
      "interval": "D",
      "timezone": "Asia/Kolkata",
      "theme": "light",
      "style": "1",
      "locale": "en",
      "toolbar_bg": "#f1f3f6",
      "enable_publishing": false,
      "allow_symbol_change": true,
      "container_id": "tradingview_chart"

      }});

      </script>

    </div>
    """

    components.html(html, height=520)


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
# MARKET OVERVIEW
# ======================

with tab1:

    st.subheader("Market Overview")

    col1,col2,col3 = st.columns(3)

    p,c = metric("^NSEI")
    p2,c2 = metric("^BSESN")
    p3,c3 = metric("^NSEBANK")

    with col1:
        st.metric("NIFTY 50",p,str(c)+"%")

    with col2:
        st.metric("SENSEX",p2,str(c2)+"%")

    with col3:
        st.metric("BANK NIFTY",p3,str(c3)+"%")

# ======================
# TOP GAINERS
# ======================

with tab2:

    st.subheader("Top Gainers")

    stocks = [
    "RELIANCE.NS","TCS.NS","INFY.NS",
    "HDFCBANK.NS","ICICIBANK.NS","SBIN.NS"
    ]

    data = yf.download(stocks, period="2d", progress=False)["Close"]

    gainers=[]

    for stock in data.columns:

        prev=data[stock].iloc[-2]
        latest=data[stock].iloc[-1]

        change=((latest-prev)/prev)*100

        gainers.append({
        "Stock":stock.replace(".NS",""),
        "Price":round(latest,2),
        "Change %":round(change,2)
        })

    df=pd.DataFrame(gainers)

    st.dataframe(df.sort_values("Change %",ascending=False))

# ======================
# SECTOR PERFORMANCE
# ======================

with tab3:

    st.subheader("Sector Performance")

    sector_data={}

    for sector in SECTOR_COMPANIES:

        stocks=SECTOR_COMPANIES[sector]

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

    st.dataframe(sector_df)

# ======================
# MARKET NEWS
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

    text="\n".join(market_news)

    prompt=f"""
Analyze sentiment of these headlines.

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

with tab5:

    st.subheader("Company Analysis")

    sector = st.selectbox("Select Sector",list(SECTOR_COMPANIES.keys()))

    company = st.selectbox("Select Company",SECTOR_COMPANIES[sector])

    symbol = company.replace(" ","").upper()

    st.subheader("TradingView Chart")

    tradingview_chart(f"NSE:{symbol}")

# ======================
# CONTACT
# ======================

with tab6:

    st.subheader("Contact")

    st.markdown("""

**Ankit Srivastava**

📞 Phone: 9616216095  
📧 Email: ankit@example.com  
💼 LinkedIn: https://linkedin.com  

Feel free to reach out for collaboration.

""")
```
