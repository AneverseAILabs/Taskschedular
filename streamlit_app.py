import streamlit as st
from groq import Groq

st.set_page_config(page_title="AI Assistant", layout="wide")

st.title("🤖 Groq AI Assistant")

# Sidebar API key
api_key = st.sidebar.text_input("Enter Groq API Key", type="password")

prompt = st.text_area("Ask something")

if st.button("Generate Response"):

    if not api_key:
        st.warning("Please enter Groq API key")

    elif prompt:

        client = Groq(api_key=api_key)

        with st.spinner("Thinking..."):

            chat = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            response = chat.choices[0].message.content

            st.subheader("Response")
            st.write(response)
