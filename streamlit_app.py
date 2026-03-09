import streamlit as st
import yfinance as yf
import pandas as pd
import feedparser
import urllib.parse
from groq import Groq

# ------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------

st.set_page_config(page_title="AI Investor Dashboard", layout="wide")

# ------------------------------------------------
# PROFESSIONAL CSS
# ------------------------------------------------

st.markdown("""
<style>

.stApp{
background-color:#f4f6f9;
}

/* title */
h1{
color:teal;
text-align:center;
font-size:42px;
margin-bottom:10px;
}

/* section headings */
h2,h3{
color:teal;
margin-top:30px;
}

/* cards */
.card{
background:white;
padding:16px;
border-radius:12px;
box-shadow:0 3px 8px rgba(0,0,0,0.08);
margin-bottom:15px;
}

/* table */
thead tr th{
background:#e6fffa;
color:teal;
font-weight:bold;
}

/* button */
.stButton > button{
background:teal;
color:white;
border-radius:8px;
padding:8px 18px;
}

/* news cards */
.news-card{
background:white;
padding:12px;
border-radius:10px;
border-left:5px solid teal;
margin-bottom:10px;
box-shadow:0 2px 6px rgba(0,0,0,0.05);
}

</style>
""", unsafe_allow_html=True)

# ------------------------------------------------
# HEADER
# ------------------------------------------------

st.title("AI Investor Dashboard")

st.write("Analyze companies, growth performance, news, and AI insights.")

# ------------------------------------------------
# COMPANY SELECT
# ------------------------------------------------

companies = {
"Reliance Industries":"RELIANCE.NS",
"TCS":"TCS.NS",
"Infosys":"INFY.NS",
"HDFC Bank":"HDFCBANK.NS",
"ICICI Bank":"ICICIBANK.NS"
}

company = st.selectbox("Select Company", list(companies.keys()))

ticker = companies[company]

# ------------------------------------------------
# STOCK DATA
# ------------------------------------------------

stock = yf.Ticker(ticker)

data = stock.history(period="max")

price = data["Close"].iloc[-1]

# ------------------------------------------------
# GROWTH FUNCTION (DATE BASED)
# ------------------------------------------------

def calc_growth(years=None, months=None, days=None):

    target = data.index[-1]

    if years:
        target = target - pd.DateOffset(years=years)

    if months:
        target = target - pd.DateOffset(months=months)

    if days:
        target = target - pd.DateOffset(days=days)

    past = data[data.index <= target]

    if len(past) == 0:
        return None

    past_price = past["Close"].iloc[-1]

    return round(((price-past_price)/past_price)*100,2)

# ------------------------------------------------
# GROWTH TABLE
# ------------------------------------------------

growth = {
"Overall": round(((price-data["Close"].iloc[0])/data["Close"].iloc[0])*100,2),
"15 Years":calc_growth(years=15),
"10 Years":calc_growth(years=10),
"5 Years":calc_growth(years=5),
"3 Years":calc_growth(years=3),
"1 Year":calc_growth(years=1),
"6 Months":calc_growth(months=6),
"3 Months":calc_growth(months=3),
"1 Week":calc_growth(days=7),
"1 Day":calc_growth(days=1)
}

growth_table = pd.DataFrame(
list(growth.items()),
columns=["Period","Growth %"]
)

st.subheader("Growth Performance")

st.markdown('<div class="card">', unsafe_allow_html=True)

st.dataframe(
growth_table.style.format({"Growth %":"{:.2f}%"}),
use_container_width=True
)

st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------------------------
# CURRENT PRICE
# ------------------------------------------------

st.subheader("Current Price")

st.markdown('<div class="card">', unsafe_allow_html=True)

st.metric("Price",f"₹{price:,.2f}")

st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------------------------
# NEWS
# ------------------------------------------------

st.subheader("Latest News")

query = urllib.parse.quote(company + " stock")

news_url = f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"

feed = feedparser.parse(news_url)

news_text=""

for entry in feed.entries[:5]:

    st.markdown(f"""
    <div class="news-card">
    <b>{entry.title}</b><br>
    <a href="{entry.link}" target="_blank">Read article</a>
    </div>
    """, unsafe_allow_html=True)

    news_text += entry.title + "\n"

# ------------------------------------------------
# AI ANALYSIS
# ------------------------------------------------

st.subheader("AI Analysis")

if st.button("Run AI Analysis"):

    client = Groq(api_key=st.secrets["GROQ_API_KEY"])

    prompt=f"""
    Analyze the stock {company}

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

# ------------------------------------------------
# CONTACT FOOTER
# ------------------------------------------------

st.markdown("""
<hr>

<div style="text-align:center;color:gray">

<h3 style="color:teal">Contact</h3>

Ankit<br>
📞 9616216095

</div>
""", unsafe_allow_html=True)
