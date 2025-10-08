# app.py (updated for openai>=1.0.0)
import os
import streamlit as st

# Use the new client from openai-python v1+
try:
    from openai import OpenAI, APIError  # APIError available in new client
except Exception:
    # Fallback if the environment is weird; still import client
    from openai import OpenAI
    APIError = Exception

st.set_page_config(page_title="Simple Chat — Streamlit Cloud (OpenAI v1+)", page_icon="💬")
st.title("Simple Chat — Streamlit Cloud (gpt-3.5-turbo)")

# Sidebar: read secrets if present (Streamlit Cloud)
secrets_key = st.secrets.get("OPENAI_API_KEY") if hasattr(st, "secrets") else None
manual_key = st.sidebar.text_input(
    "OpenAI API Key (manual, session only)", placeholder="sk-...", type="password"
)

model = st.sidebar.selectbox("Model", ["gpt-3.5-turbo"], index=0)
temperature = st.sidebar.slider("Temperature", 0.0, 1.0, 0.7, 0.05)

if st.sidebar.button("Clear chat"):
    st.session_state.pop("messages", None)
    st.experimental_rerun()

# Initialize history
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": "You are a helpful assistant."}]

# helper to render messages
def render_messages(messages):
    for m in messages:
        if m["role"] == "system":
            continue
        with st.chat_message(m["role"]):
            st.write(m["content"])

render_messages(st.session_state.messages)

# input
if prompt := st.chat_input("Type your message..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Resolve API key (secrets preferred)
    openai_api_key = secrets_key or manual_key or os.environ.get("OPENAI_API_KEY") or ""
    if not openai_api_key:
        st.error("No OpenAI API key found. Add to Streamlit Secrets or paste in the sidebar.")
    else:
        # create a client per-request (safe for small apps)
        client = OpenAI(api_key=openai_api_key)

        try:
            with st.spinner("Contacting OpenAI..."):
                # New v1+ call
                completion = client.chat.completions.create(
                    model=model,
                    messages=st.session_state.messages,
                    temperature=float(temperature),
                    max_tokens=800,
                )

            # Access assistant text (same shape as old API)
            assistant_text = completion.choices[0].message.content.strip()
            st.session_state.messages.append({"role": "assistant", "content": assistant_text})
            with st.chat_message("assistant"):
                st.write(assistant_text)

            # Show token usage if present
            usage = getattr(completion, "usage", None)
            if usage:
                prompt_tokens = getattr(usage, "prompt_tokens", None) or usage.get("prompt_tokens", None)
                completion_tokens = getattr(usage, "completion_tokens", None) or usage.get("completion_tokens", None)
                total = getattr(usage, "total_tokens", None) or usage.get("total_tokens", None)
                st.sidebar.markdown(f"**Usage:** prompt {prompt_tokens} | completion {completion_tokens} | total {total}")

        except APIError as e:
            st.error(f"OpenAI API error: {e}")
        except Exception as e:
            # Generic fallback for unexpected issues
            st.error(f"Unexpected error: {e}")

st.markdown("---")
st.markdown("⚠️ **Security note:** Use Streamlit Secrets (recommended) — don't commit keys to GitHub.")
