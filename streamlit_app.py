import streamlit as st
import yfinance as yf
import pandas as pd
from groq import Groq

st.set_page_config(page_title="AI Investor Dashboard", layout="wide")

# -------------------------
# UI STYLE
# -------------------------

st.markdown("""
<style>
.stApp {background-color:#f8fafc;}
h1,h2,h3 {color: teal;}
p,div,span {color:#6b7280;}
</style>
""", unsafe_allow_html=True)

st.title("📊 AI Investor Dashboard")

# -------------------------
# COMPANY DROPDOWN
# -------------------------

companies = {
"Reliance Industries":"RELIANCE.NS",
"TCS":"TCS.NS",
"Infosys":"INFY.NS",
"HDFC Bank":"HDFCBANK.NS",
"ICICI Bank":"ICICIBANK.NS"
}

company = st.selectbox("Select Company", list(companies.keys()))

ticker = companies[company]

# -------------------------
# STOCK DATA
# -------------------------

stock = yf.Ticker(ticker)

data = stock.history(period="10y")

price = data["Close"].iloc[-1]

# -------------------------
# GROWTH FUNCTION
# -------------------------

def calc_growth(days):

    if len(data) > days:
        old = data["Close"].iloc[-days]
        new = data["Close"].iloc[-1]
        return round(((new-old)/old)*100,2)

    return None

# -------------------------
# PERFORMANCE TABLE
# -------------------------

growth = {
"10 Years":calc_growth(252*10),
"7.5 Years":calc_growth(int(252*7.5)),
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

st.subheader("📈 Performance")

st.table(table)

# -------------------------
# PRICE
# -------------------------

st.metric("Current Price", f"₹{price:,.2f}")

# -------------------------
# NEWS SECTION
# -------------------------

st.subheader("📰 Latest News")

news = stock.news

if news:

    for item in news[:5]:

        title = item.get("title","No title available")
        link = item.get("link","")

        st.markdown(f"**{title}**")

        if link:
            st.write(link)

else:

    st.write("No news available")

# -------------------------
# AI ANALYSIS
# -------------------------

st.subheader("🤖 AI Investment Insight")

if st.button("Generate AI Analysis"):

    client = Groq(api_key=st.secrets["GROQ_API_KEY"])

    prompt = f"""
    Analyze the stock {company}.

    Current Price: {price}

    Growth performance:
    {growth}

    Provide:
    - company overview
    - strengths and risks
    - future outlook
    - recommendation (Buy/Hold/Sell)
    """

    chat = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role":"user","content":prompt}]
    )

    result = chat.choices[0].message.content

    st.write(result)
