import streamlit as st
import yfinance as yf
import pandas as pd
from groq import Groq

# ----------------------------------
# PAGE CONFIG
# ----------------------------------

st.set_page_config(page_title="AI Investor Dashboard", layout="wide")

# ----------------------------------
# CSS STYLE
# ----------------------------------

st.markdown("""
<style>

.stApp{
background-color:#f5f7fb;
}

.header{
background-color:teal;
padding:16px;
color:white;
text-align:center;
font-size:30px;
font-weight:bold;
border-radius:8px;
}

h1,h2,h3{
color:teal;
}

p,div,span{
color:#6b7280;
}

</style>
""", unsafe_allow_html=True)

# ----------------------------------
# HEADER
# ----------------------------------

st.markdown('<div class="header">AI Investor Dashboard</div>', unsafe_allow_html=True)

st.write("Analyze stocks, growth performance, news, and AI insights.")

# ----------------------------------
# COMPANY LIST
# ----------------------------------

companies = {
"Reliance Industries":"RELIANCE.NS",
"TCS":"TCS.NS",
"Infosys":"INFY.NS",
"HDFC Bank":"HDFCBANK.NS",
"ICICI Bank":"ICICIBANK.NS"
}

company = st.selectbox("Select Company", list(companies.keys()))

ticker = companies[company]

# ----------------------------------
# STOCK DATA
# ----------------------------------

stock = yf.Ticker(ticker)

data = stock.history(period="max")

price = data["Close"].iloc[-1]

# ----------------------------------
# GROWTH FUNCTION
# ----------------------------------

def calc_growth(days):

    if len(data) <= days:
        days = len(data)-1

    start = data["Close"].iloc[-days]
    end = data["Close"].iloc[-1]

    return round(((end-start)/start)*100,2)

# ----------------------------------
# PERFORMANCE TABLE
# ----------------------------------

growth = {
"Overall":calc_growth(len(data)-1),
"15 Years":calc_growth(252*15),
"10 Years":calc_growth(252*10),
"5 Years":calc_growth(252*5),
"3 Years":calc_growth(252*3),
"1 Year":calc_growth(252),
"6 Months":calc_growth(126),
"3 Months":calc_growth(63),
"1 Week":calc_growth(5),
"1 Day":calc_growth(1)
}

table = pd.DataFrame(
list(growth.items()),
columns=["Period","Growth %"]
)

st.subheader("Performance")

st.dataframe(table,use_container_width=True)

# ----------------------------------
# CURRENT PRICE
# ----------------------------------

st.metric("Current Price",f"₹{price:,.2f}")

# ----------------------------------
# NEWS
# ----------------------------------

st.subheader("Latest News")

news = stock.news

news_text=""

if news:

    for item in news[:5]:

        title=item.get("title","")

        link=item.get("link","")

        news_text += title + "\n"

        st.markdown(f"**{title}**")

        if link:
            st.write(link)

else:

    st.write("No news available")

# ----------------------------------
# AI ANALYSIS
# ----------------------------------

st.subheader("AI Analysis")

if st.button("Run AI Analysis"):

    client = Groq(api_key=st.secrets["GROQ_API_KEY"])

    prompt=f"""
    Analyze the stock {company}.

    Current Price: {price}

    Growth performance:
    {growth}

    News:
    {news_text}

    Provide:

    1. AI Investment Score (0-100)
    2. News Sentiment (Positive/Neutral/Negative)
    3. Short explanation of sentiment
    4. Growth outlook (Bullish/Moderate/Bearish)
    5. Expected growth next 12 months (%)
    """

    chat = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role":"user","content":prompt}]
    )

    result = chat.choices[0].message.content

    st.write(result)

# ----------------------------------
# FOOTER
# ----------------------------------

st.markdown("""
<hr>
<div style="text-align:center;color:gray;">
AI Investor Dashboard<br>
Contact: <b>9616216095</b>
</div>
""", unsafe_allow_html=True)
