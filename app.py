# app.py
import streamlit as st
import openai
from typing import List, Dict

st.set_page_config(page_title="Simple Chat — Streamlit Cloud", page_icon="💬")
st.title("Simple Chat — Streamlit Cloud (gpt-3.5-turbo)")

# Sidebar: settings / API key
st.sidebar.header("Settings")

# First, prefer API key from Streamlit Secrets (recommended on Streamlit Cloud)
secrets_key = None
try:
    secrets_key = st.secrets["OPENAI_API_KEY"]
except Exception:
    secrets_key = None

if secrets_key:
    st.sidebar.success("Using OpenAI key from Streamlit Secrets.")
else:
    st.sidebar.info("No OpenAI key found in Streamlit Secrets. You can paste one below (only for this session).")

# Manual API key input fallback (won't be saved to repo)
manual_key = st.sidebar.text_input(
    "OpenAI API Key (manual, session only)",
    placeholder="sk-...",
    type="password",
    help="Paste your OpenAI key here if you didn't add it to Streamlit Secrets."
)

# Choose model (default = smallest practical)
model = st.sidebar.selectbox("Model", ["gpt-3.5-turbo"], index=0)
temperature = st.sidebar.slider("Temperature", 0.0, 1.0, 0.7, 0.05)

if st.sidebar.button("Clear chat"):
    st.session_state.pop("messages", None)
    st.experimental_rerun()

# Initialize message history in session state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "You are a helpful assistant."}
    ]

# Helper to display messages
def render_messages(messages: List[Dict[str, str]]):
    for msg in messages:
        if msg["role"] == "system":
            # Optionally show a small hint for system message
            continue
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

# Render existing conversation
render_messages(st.session_state.messages)

# Chat input
if prompt := st.chat_input("Type your message..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Resolve API key (secrets preferred)
    openai_api_key = secrets_key or manual_key or ""
    if not openai_api_key:
        st.error("No OpenAI API key available. Add it to Streamlit Secrets or paste it in the sidebar.")
    else:
        openai.api_key = openai_api_key

        # Call OpenAI Chat Completions (non-streaming)
        try:
            with st.spinner("Contacting OpenAI..."):
                resp = openai.ChatCompletion.create(
                    model=model,
                    messages=st.session_state.messages,
                    temperature=float(temperature),
                    max_tokens=800,
                )

            assistant_msg = resp["choices"][0]["message"]["content"].strip()
            st.session_state.messages.append({"role": "assistant", "content": assistant_msg})
            with st.chat_message("assistant"):
                st.write(assistant_msg)

            # Show usage if available
            if "usage" in resp:
                u = resp["usage"]
                st.sidebar.markdown(
                    f"**Usage:** prompt {u.get('prompt_tokens',0)} | completion {u.get('completion_tokens',0)} | total {u.get('total_tokens',0)}"
                )

        except openai.error.OpenAIError as e:
            st.error(f"OpenAI API error: {e}")
        except Exception as e:
            st.error(f"Unexpected error: {e}")

st.markdown("---")
st.markdown(
    "⚠️ **Security note:** On Streamlit Cloud prefer using the Secrets UI (do **not** commit keys to GitHub)."
)
