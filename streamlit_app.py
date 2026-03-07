import streamlit as st
from groq import Groq
from openai import OpenAI
import google.generativeai as genai

st.title("📈 AI Investor Dashboard")

provider = st.selectbox(
    "Select AI Provider",
    ["Groq","OpenAI","Gemini"]
)

prompt = st.text_area("Ask AI about a company")

if st.button("Generate Insight"):

    if provider == "Groq":

        client = Groq(api_key=st.secrets["GROQ_API_KEY"])

        chat = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role":"user","content":prompt}]
        )

        result = chat.choices[0].message.content


    elif provider == "OpenAI":

        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"user","content":prompt}]
        )

        result = response.choices[0].message.content


    else:

        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

        model = genai.GenerativeModel("gemini-1.5-flash")

        response = model.generate_content(prompt)

        result = response.text


    st.subheader("AI Response")
    st.write(result)
