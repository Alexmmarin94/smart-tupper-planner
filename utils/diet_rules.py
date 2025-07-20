# utils/diet_rules.py

"""
This module contains heuristic rules to assign dietary attributes
to each dish based on its name, ingredients, and macronutrient profile.
These labels are later used to enrich the vector store metadata for retrieval.
"""

def is_vegetariano(ingredientes: str) -> bool:
    """
    Returns True if the dish does not contain meat or seafood,
    assuming it's suitable for a vegetarian diet.
    """
    forbidden = {"pollo", "carne", "cerdo", "jamón", "pescado", "marisco", "gamba", "atún"}
    return not any(w in ingredientes.lower() for w in forbidden)


def is_vegano(ingredientes: str) -> bool:
    """
    Returns True if the dish contains no animal-derived ingredients,
    suitable for a vegan diet.
    """
    forbidden = {
        "pollo", "carne", "cerdo", "jamón", "pescado", "marisco", "gamba", "atún",
        "leche", "queso", "mantequilla", "huevo", "nata", "miel", "yogur"
    }
    return not any(w in ingredientes.lower() for w in forbidden)


def is_keto(kcal: float, hidratos: float) -> bool:
    """
    Returns True if the dish is both calorie-dense and very low in carbs,
    aligned with a ketogenic (keto) diet.
    """
    return hidratos < 5 and kcal > 100


def bajo_en_calorias(kcal: float) -> bool:
    """
    Flags a dish as 'low-calorie' if it contains fewer than 80 kcal per 100g.
    """
    return kcal < 80


def es_postre(nombre: str, ingredientes: str) -> bool:
    """
    Attempts to classify a dish as dessert based on common sweet-related keywords
    in the dish name or ingredient list.
    """
    keywords = {"azúcar", "chocolate", "vainilla", "canela", "nata", "galleta", "dulce", "bizcocho"}
    return any(w in ingredientes.lower() or w in nombre.lower() for w in keywords)


def de_cuchara(nombre: str, ingredientes: str) -> bool:
    """
    Returns True if the dish is typically eaten with a spoon,
    based on the name of the dish.
    """
    return any(w in nombre.lower() for w in {"sopa", "crema", "guiso", "estofado", "potaje"})


def alto_proteina(proteinas: float) -> bool:
    """
    Flags dishes with more than 12g of protein per 100g as high-protein.
    """
    return proteinas > 12


def sin_lactosa(ingredientes: str) -> bool:
    """
    Returns True if no common dairy ingredients are found.
    """
    lacteos = {"leche", "nata", "queso", "mantequilla", "yogur"}
    return not any(w in ingredientes.lower() for w in lacteos)


def no_congelar(ingredientes: str, nombre: str) -> bool:
    """
    Flags dishes that should not be frozen due to ingredients
    known to degrade in texture or safety after freezing.
    """
    lowfreeze = {"patata", "pasta", "leche", "nata", "yogur", "mayonesa", "huevo", "queso"}
    text = (ingredientes + " " + nombre).lower()
    return any(w in text for w in lowfreeze)


def apto_congelar(ingredientes: str, nombre: str) -> bool:
    """
    Returns True if the dish contains none of the problematic
    ingredients for freezing.
    """
    return not no_congelar(ingredientes, nombre)


def sin_gluten(ingredientes: str) -> bool:
    """
    Returns True if no gluten-containing ingredients are detected.
    This is a best-effort heuristic, not medically reliable.
    """
    gluten = {"trigo", "cebada", "centeno", "espelta", "kamut", "galleta", "harina"}
    return not any(w in ingredientes.lower() for w in gluten)


def apply_heuristics(row: dict) -> dict:
    """
    Applies all dietary rule functions to a given dish row.
    The row should contain fields: 'kcal', 'hidratos', 'proteinas', 'ingredientes', 'nombre_plato'.

    Returns a dictionary with all inferred binary attributes.
    """
    kcal = float(row.get("kcal") or 0)
    hidr = float(row.get("hidratos") or 0)
    prot = float(row.get("proteinas") or 0)
    ing = row.get("ingredientes", "")
    nom = row.get("nombre_plato", "")

    return {
        "is_vegano": is_vegano(ing),
        "is_vegetariano": is_vegetariano(ing),
        "is_keto": is_keto(kcal, hidr),
        "bajo_en_calorias": bajo_en_calorias(kcal),
        "es_postre": es_postre(nom, ing),
        "de_cuchara": de_cuchara(nom, ing),
        "alto_proteina": alto_proteina(prot),
        "sin_lactosa": sin_lactosa(ing),
        "sin_gluten": sin_gluten(ing),
        "congelar": apto_congelar(ing, nom)
    }
