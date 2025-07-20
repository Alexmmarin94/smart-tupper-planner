from bs4 import BeautifulSoup
import pandas as pd
import re

def extract_dishes_from_html(html_path):
    """
    Parses the raw HTML file from Nocinomas and returns a DataFrame with nutritional and descriptive information.

    Expected output DataFrame columns:
        - 'nombre_plato': Name of the dish
        - 'ingredientes': Ingredients list (string)
        - 'precio': Price in euros (float)
        - 'kcal': Calories (float)
        - 'proteinas': Protein content in grams (float)
        - 'hidratos': Carbohydrates in grams (float)
        - 'grasas': Fats in grams (float)
        - 'peso': Net weight of the dish in grams (float)
        - 'alergenos': Allergens present in the dish (string)
    """

    # Load the HTML content and parse with BeautifulSoup
    with open(html_path, encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    result = []

    """
    The HTML structure from the Nocinomas website separates dish descriptions and pricing
    into two parallel blocks: one for nutritional and textual info (`td.report`),
    and another for prices (`td.price`). These are aligned by index.
    """
    report_blocks = soup.find_all("td", class_="report")
    price_blocks = soup.find_all("td", class_="price")

    # Iterate over each dish block and extract relevant fields
    for i, report in enumerate(report_blocks):
        nombre_tag = report.find("span", class_="tupper")
        ingredientes_tag = report.find("span", class_="ingredientes")
        kcal_tag = report.find("span", class_="energia")
        proteinas_tag = report.find("span", class_="proteinas")
        hidratos_tag = report.find("span", class_="hidratos")
        grasas_tag = report.find("span", class_="grasas")
        peso_tag = report.find("span", class_="peso")
        alergenos_tag = report.find("span", class_="alergenos")

        # Match the price by index (if it exists)
        precio_tag = price_blocks[i] if i < len(price_blocks) else None

        # Only process valid entries (must have name and ingredients)
        if nombre_tag and ingredientes_tag:
            result.append({
                "nombre_plato": clean_nombre(nombre_tag),
                "ingredientes": ingredientes_tag.get_text(strip=True),
                "precio": clean_float(precio_tag),
                "kcal": clean_float(kcal_tag),
                "proteinas": clean_float(proteinas_tag),
                "hidratos": clean_float(hidratos_tag),
                "grasas": clean_float(grasas_tag),
                "peso": clean_float(peso_tag),
                "alergenos": alergenos_tag.get_text(strip=True) if alergenos_tag else None
            })

    return pd.DataFrame(result)


def clean_float(tag):
    """
    Extracts the first floating-point number from the given tag's text.

    This function is robust to European decimal formats (commas) and fallback scenarios
    where the tag may be missing or malformed.
    """
    if tag:
        # Normalize decimal commas to dots
        text = tag.get_text(strip=True).replace(",", ".")
        # Extract the first number found in the text (int or float)
        match = re.search(r"[-+]?\d*\.\d+|\d+", text)
        return float(match.group()) if match else None
    return None


def clean_nombre(tag):
    """
    Cleans and returns the dish name.

    Dish names are sometimes formatted with a trailing colon (e.g., "Tortilla de espinacas:"),
    which we remove here.
    """
    text = tag.get_text(strip=True)
    return text.rstrip(":")
