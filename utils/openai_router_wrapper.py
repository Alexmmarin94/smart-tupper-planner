import os
from dotenv import load_dotenv

# Load local .env variables (if available)
load_dotenv()

# Try to import Streamlit and check if secrets exist
try:
    import streamlit as st
    has_streamlit_secrets = True
except ImportError:
    has_streamlit_secrets = False

def get_env_var(key: str):
    """
    Returns the value of an environment variable or Streamlit secret.
    Priority:
    1. Streamlit secrets (if running in Streamlit and key exists)
    2. os.environ (from .env or system)
    """
    if has_streamlit_secrets and key in st.secrets:
        value = st.secrets[key]
        print(f"[INFO] Read from secrets.toml: {key} = {value}")
        return value

    value = os.getenv(key)
    if value:
        print(f"[INFO] Read from .env or environment: {key} = {value}")
    return value

# Retrieve config values
api_key = get_env_var("OPENROUTER_API_KEY")
base_url = get_env_var("OPENROUTER_BASE_URL")
model = get_env_var("LLM_MODEL")

# Fail explicitly if any required key is missing
missing = [k for k, v in {
    "OPENROUTER_API_KEY": api_key,
    "OPENROUTER_BASE_URL": base_url,
    "LLM_MODEL": model
}.items() if not v]

if missing:
    raise RuntimeError(f"Missing config keys: {', '.join(missing)}")

# LangChain wrapper
from langchain_openai.chat_models import ChatOpenAI

class ChatOpenRouter(ChatOpenAI):
    def __init__(self, **kwargs):
        super().__init__(
            model=model,
            openai_api_key=api_key,
            base_url=base_url,
            **kwargs
        )
