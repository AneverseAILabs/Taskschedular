import streamlit as st
import yfinance as yf
from groq import Groq

st.set_page_config(page_title="AI Investor Dashboard", layout="wide")

st.title("📈 AI Investor Dashboard")

# --------------------------------------
# Company Dropdown
# --------------------------------------

companies = {
"Reliance Industries":"RELIANCE.NS",
"TCS":"TCS.NS",
"Infosys":"INFY.NS",
"HDFC Bank":"HDFCBANK.NS",
"ICICI Bank":"ICICIBANK.NS",
"ITC":"ITC.NS",
"Larsen & Toubro":"LT.NS"
}

company = st.selectbox("Select Company", list(companies.keys()))

ticker = companies[company]

stock = yf.Ticker(ticker)

data = stock.history(period="10y")

# --------------------------------------
# Growth Metrics
# --------------------------------------

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

# --------------------------------------
# Latest News
# --------------------------------------

st.subheader("📰 Latest News")

news = stock.news

if news:

    for item in news[:5]:

        title = item.get("title","No title")

        link = item.get("link","")

        st.markdown(f"**{title}**")

        if link:
            st.write(link)

else:

    st.write("No news available")

# --------------------------------------
# Acquisition Detection
# --------------------------------------

st.subheader("🤝 Acquisitions / Mergers")

keywords = ["acquisition","acquire","merger","stake","buy"]

for item in news:

    title = item.get("title","").lower()

    if any(k in title for k in keywords):

        st.write("🔹",item.get("title",""))

# --------------------------------------
# AI Guidance
# --------------------------------------

st.subheader("🧠 AI Investment Guidance")

if st.button("Generate AI Insight"):

    client = Groq(api_key=st.secrets["GROQ_API_KEY"])

    prompt = f"""
    Provide investment guidance for {company}

    Growth metrics:
    10Y: {growth["10Y"]}%
    5Y: {growth["5Y"]}%
    1Y: {growth["1Y"]}%

    Provide:
    - Company outlook
    - Key risks
    - Recommendation (Buy/Hold/Sell)
    """

    chat = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role":"user","content":prompt}]
    )

    result = chat.choices[0].message.content

    st.write(result)
