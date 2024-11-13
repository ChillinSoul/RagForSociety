import json
import os
import re
from bs4 import BeautifulSoup
import markdownify
import html2text

# Fichiers
input_file = "scraped_data.json"
output_file = "converted_to_markdown.json"
markdown_output_file = "output_page.md"

# Charger le fichier JSON contenant les données HTML brutes
if os.path.exists(input_file):
    with open(input_file, 'r') as file:
        scraped_data = json.load(file)
else:
    print(f"Le fichier {input_file} n'existe pas.")
    exit()

# Fonction pour nettoyer les sauts de lignes multiples et les espaces blancs
def clean_text(text):
    text = re.sub(r'\n+', '\n', text)  # Réduire les sauts de ligne multiples à un seul
    text = re.sub(r'[ \t]+', ' ', text)  # Remplacer les espaces multiples par un seul
    return text.strip()

# Fonction pour convertir le HTML en Markdown avec markdownify, en ignorant les images
def convert_with_markdownify(html_content):
    return markdownify.markdownify(html_content, heading_style="ATX", strip=["img"])

# Fonction pour convertir le HTML en Markdown avec html2text, en ignorant les images
def convert_with_html2text(html_content):
    handler = html2text.HTML2Text()
    handler.ignore_images = True  # Ignorer les images
    handler.ignore_links = False  # Inclure les liens
    handler.body_width = 0  # Désactiver la limitation de la largeur des lignes
    return handler.handle(html_content)

# Extraire et traiter un seul lien pour le test
url, page_data = next(iter(scraped_data.items()))
html_content = page_data['content']

# Décoder les caractères d'échappement
html_content = html_content.encode().decode('unicode_escape')

# Convertir avec markdownify
markdown_text = convert_with_markdownify(html_content)
markdown_text = clean_text(markdown_text)

# Convertir avec html2text
html2text_output = convert_with_html2text(html_content)
html2text_output = clean_text(html2text_output)

# Sauvegarder les résultats dans un fichier JSON structuré
converted_data = {
    url: {
        "title": page_data['title'],
        "url": url,
        "converted_with_markdownify": markdown_text,
        "converted_with_html2text": html2text_output
    }
}

with open(output_file, 'w') as file:
    json.dump(converted_data, file, indent=4)

# Sauvegarder le contenu Markdown dans un fichier .md
with open(markdown_output_file, 'w', encoding='utf-8') as file:
    file.write(f"# {page_data['title']}\n\n{markdown_text}\n")

print(f"Conversion terminée pour {url}. Les résultats sont sauvegardés dans {output_file} et {markdown_output_file}.")
