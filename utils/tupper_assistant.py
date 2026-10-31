# utils/tupper_assistant.py

__import__("pysqlite3")
import sys

sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")

from pathlib import Path

from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain.chains.combine_documents import create_stuff_documents_chain

from utils.openai_router_wrapper import ChatOpenRouter


# -----------------------------------------------------------------------------
# VECTORSTORE SETUP
# -----------------------------------------------------------------------------

base_dir = Path(__file__).resolve().parent
chroma_path = base_dir.parent / "chroma_db"

embedding = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

try:
    vectordb = Chroma(
        persist_directory=str(chroma_path),
        embedding_function=embedding,
        collection_name="menu_platos",
    )
except Exception:
    # Preserve the existing in-memory fallback.
    vectordb = Chroma(
        embedding_function=embedding,
        collection_name="menu_platos",
    )

all_docs = vectordb.similarity_search("plato", k=300)


# -----------------------------------------------------------------------------
# FILTER EXTRACTION
# -----------------------------------------------------------------------------

parser = JsonOutputParser()

filter_prompt = PromptTemplate.from_template(
    """
Eres un asistente que extrae filtros estructurados de preguntas sobre comida.
La respuesta debe ser un JSON válido y NADA MÁS. No expliques nada.

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
"""
).partial(format_instructions=parser.get_format_instructions())

filter_chain = (
    filter_prompt
    | ChatOpenRouter(temperature=0.1, max_tokens=512)
    | parser
)


# -----------------------------------------------------------------------------
# METADATA FILTERING
# -----------------------------------------------------------------------------

def apply_filters(docs, filters):
    """Apply structured filters to document metadata."""
    result = docs

    for key, val in filters.items():
        if key == "kcal":
            val = val.replace(" ", "")

            if val.startswith("<"):
                result = [
                    d
                    for d in result
                    if d.metadata.get("kcal", 9999) < float(val[1:])
                ]
            elif val.startswith(">"):
                result = [
                    d
                    for d in result
                    if d.metadata.get("kcal", 0) > float(val[1:])
                ]
        else:
            result = [
                d for d in result if d.metadata.get(key) == val
            ]

    return result


# -----------------------------------------------------------------------------
# DOCUMENT FORMATTING
# -----------------------------------------------------------------------------

def format_doc(doc: Document) -> Document:
    """Include dish metadata in the context passed to the model."""
    meta = doc.metadata

    extras = "\n".join(
        [
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
            f"- Apto para congelar: {meta.get('congelar')}",
        ]
    )

    return Document(
        page_content=f"{doc.page_content}\n\n{extras}",
        metadata=meta,
    )


# -----------------------------------------------------------------------------
# APPROXIMATE MATCH SCORING
# -----------------------------------------------------------------------------

def score_approx_match(doc: Document, filters: dict) -> float:
    """Score approximate matches when strict filtering returns few dishes."""
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
                score += min(proteinas / 5, 2.5)

        elif isinstance(val, bool):
            if meta.get(key) == val:
                score += 1.0
            elif (
                key in ["is_vegetariano", "is_vegano"]
                and meta.get(key) is False
            ):
                return -1.0

    return score


def should_use_fallback(question: str, formatted_docs: list) -> bool:
    """Use a larger minimum selection when the question asks for variety."""
    base_threshold = 3
    extended_threshold = 5

    keywords = [
        "semana",
        "semanas",
        "plan",
        "planificar",
        "almuerzos",
        "platos",
        "comidas",
        "días",
        "repetir",
        "menú",
        "distintos",
        "opciones",
        "tuppers",
    ]

    needs_variety = any(
        word in question.lower() for word in keywords
    )

    min_required = (
        extended_threshold if needs_variety else base_threshold
    )

    return len(formatted_docs) < min_required


# -----------------------------------------------------------------------------
# FINAL ANSWER GENERATION
# -----------------------------------------------------------------------------

qa_prompt = PromptTemplate.from_template(
    """
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
"""
)

qa_chain = create_stuff_documents_chain(
    llm=ChatOpenRouter(temperature=0, max_tokens=2048),
    prompt=qa_prompt,
)


# -----------------------------------------------------------------------------
# MAIN PIPELINE
# -----------------------------------------------------------------------------

def get_answer_to_question(question: str) -> str:
    """Extract filters, select dishes, and generate the final answer."""
    try:
        filters = filter_chain.invoke({"question": question})
    except Exception as exc:
        raise RuntimeError(
            f"Filter extraction failed ({type(exc).__name__}): {exc}"
        ) from exc

    filtered_docs = apply_filters(all_docs, filters)
    formatted_docs = [
        format_doc(doc) for doc in filtered_docs
    ]

    if should_use_fallback(question, formatted_docs):
        fallback_candidates = [
            doc for doc in all_docs if doc not in filtered_docs
        ]

        scored_fallbacks = sorted(
            fallback_candidates,
            key=lambda d: score_approx_match(d, filters),
            reverse=True,
        )

        scored_fallbacks = [
            d
            for d in scored_fallbacks
            if score_approx_match(d, filters) > 0
        ]

        formatted_docs += [
            format_doc(doc) for doc in scored_fallbacks[:10]
        ]

    response = qa_chain.invoke(
        {
            "context": formatted_docs,
            "question": question,
        }
    )

    return response
