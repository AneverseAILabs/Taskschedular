import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from groq import Groq

# ------------------------------------
# PAGE CONFIG
# ------------------------------------

st.set_page_config(page_title="AI Investor Dashboard", layout="wide")

# ------------------------------------
# UI STYLE
# ------------------------------------

st.markdown("""
<style>
.stApp {background-color:#f8fafc;}
h1,h2,h3 {color: teal;}
p,div,span {color:#6b7280;}
</style>
""", unsafe_allow_html=True)

st.title("📈 AI Investor Dashboard")

# ------------------------------------
# COMPANY DROPDOWN
# ------------------------------------

companies = {
"Reliance Industries":"RELIANCE.NS",
"TCS":"TCS.NS",
"Infosys":"INFY.NS",
"HDFC Bank":"HDFCBANK.NS",
"ICICI Bank":"ICICIBANK.NS"
}

company = st.selectbox("Select Company", list(companies.keys()))

ticker = companies[company]

# ------------------------------------
# TIME RANGE
# ------------------------------------

period = st.selectbox(
"Select Time Range",
["10y","7y","5y","3y","1y","6mo","3mo","1mo","5d","1d"]
)

# ------------------------------------
# STOCK DATA
# ------------------------------------

stock = yf.Ticker(ticker)

data = stock.history(period=period)

# ------------------------------------
# CHART
# ------------------------------------

fig = go.Figure()

fig.add_trace(go.Scatter(
x=data.index,
y=data["Close"],
mode="lines",
line=dict(color="teal",width=3)
))

fig.update_layout(
template="plotly_white",
height=450
)

st.plotly_chart(fig,width="stretch")

# ------------------------------------
# METRICS
# ------------------------------------

price = data["Close"].iloc[-1]

col1,col2,col3 = st.columns(3)

col1.metric("Current Price",f"₹{price:,.2f}")

col2.metric("High",f"₹{data['Close'].max():,.2f}")

col3.metric("Low",f"₹{data['Close'].min():,.2f}")

# ------------------------------------
# AI ANALYSIS
# ------------------------------------

st.subheader("🤖 AI Stock Analysis")

if st.button("Generate AI Insight"):

    client = Groq(api_key=st.secrets["GROQ_API_KEY"])

    prompt = f"""
    Analyze the stock {company}.

    Current Price: {price}
    Period: {period}

    Provide:
    - short company overview
    - investment outlook
    - potential risks
    - recommendation (Buy / Hold / Sell)
    """

    chat = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role":"user","content":prompt}]
    )

    result = chat.choices[0].message.content

    st.write(result)
