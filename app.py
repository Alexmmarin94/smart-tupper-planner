# app.py

__import__("pysqlite3")
import sys
import logging

sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")

import streamlit as st

logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="Nococinomas Assistant",
    page_icon="🥗",
)

ERROR_MESSAGE = (
    "Algo salió mal. Por favor, contacta a alexbmeist@gmail.com."
)

# Handle initialization errors without exposing technical details.
try:
    from utils.tupper_assistant import get_answer_to_question
except Exception:
    logger.exception("Assistant initialization failed")
    st.error(ERROR_MESSAGE)
    st.stop()

st.title("🥗 Nococinomas Assistant")
st.markdown(
    "Describe tus preferencias o restricciones dietéticas. Por ejemplo:"
)

with st.expander("Ejemplos"):
    st.markdown(
        """
- *Quiero platos vegetarianos altos en proteína*
- *Soy diabético y necesito tuppers bajos en calorías para la semana*
- *Me gustarían opciones sin lactosa y aptas para congelar*
"""
    )

user_question = st.text_input(
    "Tu pregunta",
    placeholder=(
        "Ej: Quiero platos bajos en calorías y sin gluten "
        "para cenar durante una semana"
    ),
)

if user_question:
    with st.spinner("Pensando..."):
        try:
            response = get_answer_to_question(user_question)
        except Exception:
            # Keep technical details in server logs.
            logger.exception("Answer generation failed")
            st.error(ERROR_MESSAGE)
        else:
            st.success("Esto es lo que encontré:")
            st.markdown(response)

st.markdown("---")
st.markdown(
    "🔗 [Visita nococinomas.es](https://www.nococinomas.es/)"
)
