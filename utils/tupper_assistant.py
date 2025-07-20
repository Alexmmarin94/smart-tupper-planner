# utils/tupper_assistant.py

__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')


from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain.chains.combine_documents import create_stuff_documents_chain
from utils.openai_router_wrapper import ChatOpenRouter
import os
from dotenv import load_dotenv
from pathlib import Path


# -----------------------------------------------------------------------------
# VECTORSTORE SETUP (CHROMA + EMBEDDINGS)
# -----------------------------------------------------------------------------

"""
We use an absolute path to ensure the vectorstore directory is resolved correctly
regardless of the current working directory at runtime. This is especially important
when launching the app with Streamlit (e.g., `streamlit run`), which changes the
current working directory to the root of the project. Using relative paths like
"chroma_db" from inside a subfolder such as `utils/` would then fail silently
or point to the wrong location. Resolving the path from the file location ensures
consistency across environments.
"""
base_dir = Path(__file__).resolve().parent
chroma_path = base_dir.parent / "chroma_db"

# Load embeddings model for document similarity
embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# Connect to Chroma DB
try:
    # Try loading from disk (for local development)
    vectordb = Chroma(
        persist_directory=str(chroma_path),
        embedding_function=embedding,
        collection_name="menu_platos"
    )
except:
    # Fallback to in-memory (for Streamlit Cloud)
    vectordb = Chroma(
        embedding_function=embedding,
        collection_name="menu_platos"
    )


# Retrieve and cache documents for future operations (broad query for dish-related docs)
all_docs = vectordb.similarity_search("plato", k=300)

# -----------------------------------------------------------------------------
# FILTERING SETUP USING LLM
# -----------------------------------------------------------------------------

# JSON parser to extract structured filter info
parser = JsonOutputParser()

# Prompt to ask the LLM to extract filters in JSON format (used for narrowing down dishes)
filter_prompt = PromptTemplate.from_template("""
Eres un asistente que extrae filtros estructurados de preguntas sobre comida. La respuesta debe ser un JSON válido y NADA MÁS. No expliques nada.

Devuelve solo las claves relevantes entre:
- is_vegetariano: booleano
- is_vegano: booleano
- is_keto: booleano
- bajo_en_calorias: booleano
- es_postre: booleano
- de_cuchara: booleano
- alto_proteina: booleano
- sin_lactosa: booleano
- is_gourmet: booleano
- para_diabeticos: booleano
- sin_gluten: booleano
- congelar: booleano
- kcal: cadena de comparación como "<400" o ">500"

Pregunta: {question}

{format_instructions}
""").partial(format_instructions=parser.get_format_instructions())

# Chain to extract filters via LLM
filter_chain = filter_prompt | ChatOpenRouter(temperature=0.1) | parser

# -----------------------------------------------------------------------------
# APPLY STRUCTURED FILTERS TO METADATA
# -----------------------------------------------------------------------------

def apply_filters(docs, filters):
    """
    Applies the parsed filters to the list of documents.
    Each filter checks a metadata field and filters out documents that don't match.
    Special handling is applied for kcal ranges (e.g., <400, >500).
    """
    result = docs
    for key, val in filters.items():
        if key == "kcal":
            val = val.replace(" ", "")
            if val.startswith("<"):
                result = [d for d in result if d.metadata.get("kcal", 9999) < float(val[1:])]
            elif val.startswith(">"):
                result = [d for d in result if d.metadata.get("kcal", 0) > float(val[1:])]
        else:
            result = [d for d in result if d.metadata.get(key) == val]
    return result

# -----------------------------------------------------------------------------
# DOCUMENT FORMATTER FOR FINAL QA CONTEXT
# -----------------------------------------------------------------------------

def format_doc(doc: Document) -> Document:
    """
    Format the document to include a readable bullet-point summary of metadata fields.
    This is used to provide a clear context for the LLM when generating final answers.
    """
    meta = doc.metadata
    extras = "\n".join([
        f"- Alergenos: {meta.get('alergenos', 'Desconocido')}",
        f"- Kcal: {meta.get('kcal')}",
        f"- Proteínas: {meta.get('proteinas')}",
        f"- Hidratos: {meta.get('hidratos')}",
        f"- Grasas: {meta.get('grasas')}",
        f"- Peso: {meta.get('peso')}g",
        f"- Precio: {meta.get('precio')} euros",
        f"- Sin gluten: {meta.get('sin_gluten')}",
        f"- Sin lactosa: {meta.get('sin_lactosa')}",
        f"- Es postre: {meta.get('es_postre')}",
        f"- De cuchara: {meta.get('de_cuchara')}",
        f"- Bajo en calorías: {meta.get('bajo_en_calorias')}",
        f"- Alto en proteína: {meta.get('alto_proteina')}",
        f"- Vegetariano: {meta.get('is_vegetariano')}",
        f"- Vegano: {meta.get('is_vegano')}",
        f"- Keto: {meta.get('is_keto')}",
        f"- Gourmet: {meta.get('is_gourmet')}",
        f"- Para diabéticos: {meta.get('para_diabeticos')}",
        f"- Apto para congelar: {meta.get('congelar')}"
    ])
    return Document(page_content=f"{doc.page_content}\n\n{extras}", metadata=meta)

# -----------------------------------------------------------------------------
# FALLBACK SCORING WHEN STRICT FILTERS FAIL
# -----------------------------------------------------------------------------

def score_approx_match(doc: Document, filters: dict) -> float:
    """
    Computes a fallback score for a document when strict filters return too few results.

    - For boolean fields: +1 if the field matches.
    - For "kcal": +1 if it meets the threshold.
    - For "alto_proteina": score increases based on protein content.
    - If explicitly vegetarian/vegan is requested and the item is NOT, score = -1.

    This allows approximate prioritization of documents that "almost" match.
    """
    meta = doc.metadata
    score = 0.0
    for key, val in filters.items():
        if key == "kcal":
            kcal = meta.get("kcal")
            if isinstance(kcal, (int, float)) and isinstance(val, str):
                val = val.replace(" ", "")
                if val.startswith("<") and kcal < float(val[1:]):
                    score += 1.0
                elif val.startswith(">") and kcal > float(val[1:]):
                    score += 1.0
        elif key == "alto_proteina" and val is True:
            proteinas = meta.get("proteinas")
            if isinstance(proteinas, (int, float)):
                score += min(proteinas / 5, 2.5)  # Up to 2.5 points based on protein
        elif isinstance(val, bool):
            if meta.get(key) == val:
                score += 1.0
            elif key in ["is_vegetariano", "is_vegano"] and meta.get(key) is False:
                return -1.0  # Penalize strongly if explicitly requested and not matching
    return score

# -----------------------------------------------------------------------------
# RULE TO DECIDE WHETHER TO FALLBACK
# -----------------------------------------------------------------------------

def should_use_fallback(question: str, formatted_docs: list) -> bool:
    """
    Decides if fallback is necessary:
    - If the number of matched documents is too small, fallback is triggered.
    - If the user asks for variety (keywords like "semana", "días", "opciones"),
      the threshold increases to ensure a wider selection is considered.
    """
    base_threshold = 3
    extended_threshold = 5
    keywords = [
        "semana", "semanas", "plan", "planificar", "almuerzos", "platos",
        "comidas", "días", "repetir", "menú", "distintos", "opciones", "tuppers"
    ]
    needs_variety = any(word in question.lower() for word in keywords)
    min_required = extended_threshold if needs_variety else base_threshold
    return len(formatted_docs) < min_required

# -----------------------------------------------------------------------------
# FINAL QA PROMPT TO GENERATE RECOMMENDATIONS
# -----------------------------------------------------------------------------

qa_prompt = PromptTemplate.from_template("""
Eres un asistente de Nococinomas, una tienda online de tuppers saludables y variados.

Tu función es:
- Ayudar al usuario a planificar sus pedidos según sus necesidades (dieta, presupuesto, preferencias).
- Recomendar solo platos que están disponibles en el catálogo proporcionado (NO inventes combinaciones ni menciones platos fuera del contexto).
- Priorizar los platos que mejor se ajusten a lo que pide el usuario (ej: más proteína, menor precio, etc.).
- Si el usuario menciona días o semanas, puedes sugerir repeticiones razonables, pero siempre a partir de los platos reales del contexto.
- Limita la lista a los 3–5 platos más relevantes, con sus detalles (proteínas, precio, etc.).
- No expliques el funcionamiento del sistema ni menciones que estás usando un modelo.

Platos disponibles:
{context}

Solicitud del usuario:
{question}

Tu respuesta (concreta, clara, basada solo en los platos reales):
""")

qa_chain = create_stuff_documents_chain(
    llm=ChatOpenRouter(temperature=0),
    prompt=qa_prompt
)

# -----------------------------------------------------------------------------
# MAIN ENTRY POINT: FULL PIPELINE TO GET RECOMMENDATION
# -----------------------------------------------------------------------------

def get_answer_to_question(question: str) -> str:
    """
    Main callable pipeline:
    1. Extracts filters from the question.
    2. Applies strict filters to dish documents.
    3. If too few matches, uses fallback scoring to add approximate matches.
    4. Formats the final context.
    5. Generates a natural language answer with recommendations.
    """
    try:
        filters = filter_chain.invoke({"question": question})
    except Exception:
        return "❌ No se pudieron interpretar los filtros de la pregunta."

    filtered_docs = apply_filters(all_docs, filters)
    formatted_docs = [format_doc(doc) for doc in filtered_docs]

    # If too few matches, fallback with approximate scoring
    if should_use_fallback(question, formatted_docs):
        fallback_candidates = [doc for doc in all_docs if doc not in filtered_docs]
        scored_fallbacks = sorted(
            fallback_candidates,
            key=lambda d: score_approx_match(d, filters),
            reverse=True
        )
        # Only add documents with positive score
        scored_fallbacks = [d for d in scored_fallbacks if score_approx_match(d, filters) > 0]
        formatted_docs += [format_doc(doc) for doc in scored_fallbacks[:10]]

    # Final LLM generation based on filtered + fallback-enriched documents
    response = qa_chain.invoke({
        "context": formatted_docs,
        "question": question
    })

    return response
