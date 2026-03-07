import streamlit as st
import yfinance as yf
from groq import Groq

# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------

st.set_page_config(page_title="AI Investor Dashboard", layout="wide")

# ---------------------------------------------------
# COLOR STYLE
# ---------------------------------------------------

st.markdown("""
<style>

/* App background */
.stApp {
background-color:#f5f7fb;
}

/* Main title */
h1 {
color:#7c3aed;
text-align:center;
font-weight:800;
}

/* Section headings */
h2,h3 {
color:#0f766e;
font-weight:600;
}

/* Card container */
.card {
background:white;
padding:20px;
border-radius:12px;
box-shadow:0px 6px 14px rgba(0,0,0,0.08);
margin-bottom:20px;
}

/* Metric cards */
[data-testid="stMetric"] {
background:#ecfeff;
padding:15px;
border-radius:10px;
border:1px solid #cffafe;
}

/* Buttons */
.stButton>button {
background:linear-gradient(90deg,#7c3aed,#0ea5e9);
color:white;
border:none;
border-radius:8px;
padding:10px 18px;
font-weight:600;
}

/* Select box */
div[data-baseweb="select"] {
background:white;
border-radius:8px;
}

/* News items */
.news-card {
background:#ffffff;
padding:15px;
border-radius:10px;
border-left:4px solid #7c3aed;
margin-bottom:10px;
}

</style>
""", unsafe_allow_html=True)

st.title("📈 AI Investor Dashboard")

# ---------------------------------------------------
# COMPANY LIST
# ---------------------------------------------------

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

# ---------------------------------------------------
# STOCK STATS
# ---------------------------------------------------

info = stock.info

st.subheader("📊 Company Stats")

col1,col2,col3 = st.columns(3)

col1.metric("Market Cap", info.get("marketCap"))
col2.metric("PE Ratio", info.get("trailingPE"))
col3.metric("Dividend Yield", info.get("dividendYield"))

# ---------------------------------------------------
# GROWTH METRICS
# ---------------------------------------------------

st.subheader("📈 Growth Performance")

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

# ---------------------------------------------------
# NEWS
# ---------------------------------------------------

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

# ---------------------------------------------------
# ACQUISITION / MERGER
# ---------------------------------------------------

st.subheader(" Acquisitions / Mergers")

keywords = ["acquisition","acquire","merger","stake","buy"]

found = False

for item in news:

    title = item.get("title","").lower()

    if any(k in title for k in keywords):

        st.write("🔹",item.get("title",""))
        found = True

if not found:
    st.write("No acquisition related news found")

# ---------------------------------------------------
# AI GUIDANCE
# ---------------------------------------------------

st.subheader(" AI Investment Guidance")

if st.button("Generate AI Insight"):

    client = Groq(api_key=st.secrets["GROQ_API_KEY"])

    prompt = f"""
    Provide investment guidance for {company}

    Growth metrics:
    10Y: {growth["10Y"]}%
    5Y: {growth["5Y"]}%
    1Y: {growth["1Y"]}%

    Company stats:
    Market Cap: {info.get("marketCap")}
    PE Ratio: {info.get("trailingPE")}

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
