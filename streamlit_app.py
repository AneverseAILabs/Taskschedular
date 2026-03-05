import streamlit as st
from google import genai
import os

# Page configuration
st.set_page_config(page_title="Gemini AI Assistant", layout="wide")

# Custom CSS styling
st.markdown("""
<style>

.stApp {
    background-color: #f5f6fa;
}

h1 {
    color: #1f4e79;
    text-align: center;
}

.stTextArea textarea {
    background-color: #ffffff;
    border-radius: 10px;
    border: 1px solid #dcdcdc;
}

.stButton button {
    background-color: #2b6cb0;
    color: white;
    border-radius: 8px;
    height: 40px;
    width: 200px;
    font-weight: bold;
}

.stButton button:hover {
    background-color: #1e4f8a;
}

.response-box {
    background-color: white;
    padding: 20px;
    border-radius: 10px;
    border-left: 5px solid #2b6cb0;
    margin-top: 20px;
}

</style>
""", unsafe_allow_html=True)

# Title
st.title("🤖 Gemini AI Assistant")

# API key input
api_key = st.sidebar.text_input("Enter Gemini API Key", type="password")

# Initialize Gemini client
if api_key:
    client = genai.Client(api_key=api_key)

# User input
prompt = st.text_area("Ask something")

# Generate response
if st.button("Generate Response"):

    if not api_key:
        st.warning("Please enter your Gemini API key in the sidebar")

    elif prompt:
        with st.spinner("Thinking..."):

            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt
            )

            st.markdown(
                f'<div class="response-box">{response.text}</div>',
                unsafe_allow_html=True
            )

    else:
        st.warning("Please enter a question")
