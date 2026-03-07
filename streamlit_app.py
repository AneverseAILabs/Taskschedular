import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from groq import Groq

st.set_page_config(page_title="AI Investor Dashboard", layout="wide")

st.title("📈 AI Investor Dashboard")

# Groq API Key
api_key = st.text_input("Enter Groq API Key", type="password")

# Company dropdown
companies = {
"Reliance Industries":"RELIANCE.NS",
"TCS":"TCS.NS",
"Infosys":"INFY.NS",
"HDFC Bank":"HDFCBANK.NS",
"ICICI Bank":"ICICIBANK.NS",
"ITC":"ITC.NS"
}

company = st.selectbox("Select Company", list(companies.keys()))

ticker = companies[company]

stock = yf.Ticker(ticker)

data = stock.history(period="10y")

# ------------------------------------------------
# Stock Chart
# ------------------------------------------------

st.subheader("📈 Stock Chart")

fig = go.Figure()

fig.add_trace(go.Candlestick(
x=data.index,
open=data["Open"],
high=data["High"],
low=data["Low"],
close=data["Close"]
))

st.plotly_chart(fig,use_container_width=True)

# ------------------------------------------------
# Growth Metrics
# ------------------------------------------------

st.subheader("📊 Growth Performance")

def calc_growth(days):

    if len(data) > days:

        old = data["Close"].iloc[-days]

        new = data["Close"].iloc[-1]

        return round(((new-old)/old)*100,2)

    return None


growth = {
"10Y":calc_growth(252*10),
"7.5Y":calc_growth(int(252*7.5)),
"5Y":calc_growth(252*5),
"3Y":calc_growth(252*3),
"1Y":calc_growth(252),
"6M":calc_growth(126),
"3M":calc_growth(63),
"1W":calc_growth(5),
"1D":calc_growth(1)
}

cols = st.columns(len(growth))

for col,(k,v) in zip(cols,growth.items()):

    col.metric(k,f"{v}%")

# ------------------------------------------------
# News
# ------------------------------------------------

st.subheader("📰 Latest News")

news = stock.news

for item in news[:5]:

    st.write("🔹",item["title"])

    st.write(item["link"])


# ------------------------------------------------
# Acquisition / Merger Detection
# ------------------------------------------------

st.subheader("🤝 Acquisitions & Mergers")

keywords = ["acquisition","acquire","merger","stake","buy"]

for item in news:

    title = item["title"].lower()

    if any(k in title for k in keywords):

        st.write("🔹",item["title"])


# ------------------------------------------------
# AI Guidance
# ------------------------------------------------

st.subheader("🧠 AI Guidance")

if st.button("Generate AI Insight"):

    if api_key:

        client = Groq(api_key=api_key)

        prompt = f"""
        Provide investment guidance for {company}

        Growth:
        10Y: {growth["10Y"]}%
        5Y: {growth["5Y"]}%
        1Y: {growth["1Y"]}%

        Give:
        - company outlook
        - major risks
        - recommendation (Buy/Hold/Sell)
        """

        chat = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role":"user","content":prompt}]
        )

        result = chat.choices[0].message.content

        st.write(result)

    else:

        st.warning("Enter Groq API Key")
