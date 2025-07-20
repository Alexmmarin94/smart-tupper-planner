# utils/diet_agent.py

import os
from pydantic import BaseModel
from utils.openai_router_wrapper import ChatOpenRouter
from utils.diet_rules import apply_heuristics
from langchain_core.prompts import ChatPromptTemplate

"""
This module uses an LLM to infer dietary and culinary tags for each dish,
based on its ingredients, nutritional content, and contextual metadata.

Unlike `diet_rules.py`, which applies hardcoded heuristics,
this version complements the heuristics with LLM-based reasoning,
especially for nuanced fields like 'is_gourmet' or 'para_diabeticos'.

The LLM receives the full context of the dish — including name, ingredients,
macros, and a prior flagging using static rules — and can override or confirm those
based on broader reasoning and implicit knowledge (e.g., domain expertise).
"""

class DietClassification(BaseModel):
    """
    Defines the expected schema for the LLM's response.
    Each field is a boolean corresponding to a dietary or descriptive tag.
    """
    is_vegetariano: bool
    is_vegano: bool
    is_keto: bool
    bajo_en_calorias: bool
    es_postre: bool
    de_cuchara: bool
    alto_proteina: bool
    sin_lactosa: bool
    is_gourmet: bool
    para_diabeticos: bool
    sin_gluten: bool
    congelar: bool


"""
The system prompt defines explicit rules for the agent to follow when tagging each dish.
It ensures consistent logic for well-defined criteria (like kcal thresholds),
while leaving room for LLM judgment in cases like 'gourmet' or 'para_diabeticos'.

It also reminds the model to output only the final JSON response without additional explanation.
"""
SYSTEM = """
Eres un agente experto en nutrición y conservación de alimentos.
DEVOLVERÁS SOLO un JSON con EXACTAMENTE estas claves (true/false):

is_vegetariano, is_vegano, is_keto, bajo_en_calorias, es_postre,
de_cuchara, alto_proteina, sin_lactosa, is_gourmet, para_diabeticos, sin gluten, congelar.

CRITERIOS:
- 'bajo_en_calorias' se decide SOLO con Kcal < 100.
- 'sin_lactosa' no incluye bebidas vegetales (ej. leche de coco).
- 'congelar' no se permite si hay pasta, patata, huevo, mayonesa, yogur, nata, queso o condimentos fuertes.
- 'is_gourmet' y 'para_diabeticos' se infieren con juicio experto.

RESPONDE SOLO el JSON.
"""

# Prompt construction: passes structured metadata about the dish to the LLM
prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM),
    ("user",
     "Nombre: {nombre_plato}\n"
     "Ingredientes: {ingredientes}\n"
     "Precio: {precio}\n"
     "Kcal: {kcal}\n"
     "Hidratos: {hidratos}\n"
     "Proteínas: {proteinas}\n"
     "Grasas: {grasas}\n"
     "Flags previas: {existing_flags}\n"
     "RESPONDE AQUÍ:")
])

# Initialize the LLM instance with deterministic output (temperature = 0)
# Uses a wrapper to select model routing and configuration
llm = ChatOpenRouter(model=os.getenv("LLM_MODEL"), temperature=0)

# Define structured output parsing for the LLM's response
# Validates that the output conforms to the DietClassification schema
structured = llm.with_structured_output(DietClassification, method="json_schema")

# Final LangChain chain: prompt → LLM → validated structured object
chain = prompt | structured


def classify_dish(row: dict) -> DietClassification:
    """
    Applies both heuristic and LLM logic to classify a dish.

    Step-by-step:
    1. Heuristic rules are applied first using `apply_heuristics`.
       These use basic string matching and numerical cutoffs.
    2. The resulting flags (`existing_flags`) are included in the prompt as context.
       The LLM can choose to agree with, refine, or contradict these values.
    3. The full metadata (dish name, ingredients, macros, and heuristics) is sent to the LLM.
    4. The LLM returns a fully structured classification with all dietary tags.

    This enables hybrid logic: fast deterministic rules + nuanced expert inference.

    Parameters:
        row (dict): A dictionary with keys including 'nombre_plato',
        'ingredientes', 'precio', 'kcal', 'hidratos', 'proteinas', 'grasas'.

    Returns:
        DietClassification: A structured object containing all inferred tags.
    """
    heur = apply_heuristics(row)
    payload = {
        "nombre_plato": row["nombre_plato"],
        "ingredientes": row["ingredientes"],
        "precio": row["precio"],
        "kcal": row["kcal"],
        "hidratos": row["hidratos"],
        "proteinas": row["proteinas"],
        "grasas": row["grasas"],
        "existing_flags": heur
    }
    return chain.invoke(payload)
