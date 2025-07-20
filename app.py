# app.py

import streamlit as st
from utils.tupper_assistant import get_answer_to_question

st.write("API Key:", st.secrets.get("OPENROUTER_API_KEY", "Missing API Key"))
st.write("Base URL:", st.secrets.get("OPENROUTER_BASE_URL", "Missing Base URL"))
st.write("LLM Model:", st.secrets.get("LLM_MODEL", "Missing LLM Model"))

# -------------------------------------------------------------
# Streamlit app configuration
# Set page title and icon for the browser tab
# -------------------------------------------------------------
st.set_page_config(page_title="Nococinomas Assistant", page_icon="🥗")

# -------------------------------------------------------------
# App header
# Main title and brief description in Spanish for clarity
# -------------------------------------------------------------
st.title("🥗 Nococinomas Assistant")
st.markdown("Describe tus preferencias o restricciones dietéticas. Por ejemplo:")

# -------------------------------------------------------------
# Collapsible section with sample queries
# Helps guide the user on how to interact with the assistant
# -------------------------------------------------------------
with st.expander("Ejemplos"):
    st.markdown("""
    - *Quiero platos vegetarianos altos en de proteína*  
    - *Soy diabético y necesito tuppers bajos en calorías para la semana*  
    - *Me gustarían opciones sin lactosa y aptas para congelar*  
    """)

# -------------------------------------------------------------
# Input box for user query
# Uses a placeholder to suggest what kind of question to ask
# -------------------------------------------------------------
user_question = st.text_input("Tu pregunta", placeholder="Ej: Quiero platos bajos en calorías y sin gluten para cenar durante una semana")

# -------------------------------------------------------------
# Call the assistant only when the user enters a question
# Wraps the call with a spinner and error handling
# -------------------------------------------------------------
if user_question:
    with st.spinner("Pensando..."):
        try:
            # Core logic: fetch the assistant's response based on the question
            response = get_answer_to_question(user_question)

            # Display success and show the assistant’s reply
            st.success("Esto es lo que encontré:")
            st.markdown(response)
        except Exception as e:
            # Handle any unexpected error gracefully
            st.error(f"Ocurrió un error: {e}")

# -------------------------------------------------------------
# Optional: Add a footer link to the actual website
# This allows users to visit Nococinomas directly from the app
# -------------------------------------------------------------
st.markdown("---")
st.markdown("🔗 [Visita nococinomas.es](https://www.nococinomas.es/)")
