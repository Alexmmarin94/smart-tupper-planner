# utils/openai_router_wrapper.py

import os
from dotenv import load_dotenv

try:
    import streamlit as st
    has_streamlit_secrets = True
except ImportError:
    has_streamlit_secrets = False

from langchain_openai.chat_models import ChatOpenAI

# -------------------------------------------------------------
# Load environment variables (for local development)
# -------------------------------------------------------------
load_dotenv()

# -------------------------------------------------------------
# Fallback logic: prefer Streamlit secrets if available
# -------------------------------------------------------------
def get_env_var(key):
    if has_streamlit_secrets:
        try:
            return st.secrets[key]
        except Exception:
            pass
    return os.getenv(key)

api_key = get_env_var("OPENROUTER_API_KEY")
base_url = get_env_var("OPENROUTER_BASE_URL")
model = get_env_var("LLM_MODEL")

# -------------------------------------------------------------
# Fail early if anything is missing
# -------------------------------------------------------------
missing = [k for k, v in {
    "OPENROUTER_API_KEY": api_key,
    "OPENROUTER_BASE_URL": base_url,
    "LLM_MODEL": model
}.items() if not v]

if missing:
    raise ValueError(
        f"Missing required environment variables or Streamlit secrets: {', '.join(missing)}"
    )

# -------------------------------------------------------------
# LangChain wrapper using OpenRouter
# -------------------------------------------------------------
class ChatOpenRouter(ChatOpenAI):
    def __init__(self, **kwargs):
        super().__init__(
            model=model,
            openai_api_key=api_key,
            base_url=base_url,
            **kwargs
        )
