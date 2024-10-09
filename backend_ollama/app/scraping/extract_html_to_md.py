import json
import os
import re
import random
import markdownify
import html2text

# Fichiers
input_file = "scraped_data.json"
output_file = "converted_to_markdown.json"
markdown_output_file = "output_sample_page.md"

# Charger le fichier JSON en spécifiant UTF-8
if not os.path.exists(input_file):
    print(f"Le fichier {input_file} n'existe pas.")
    exit()

with open(input_file, 'r', encoding='utf-8') as file:
    scraped_data = json.load(file)

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

# Fonction pour nettoyer le contenu Markdown
def clean_markdown_content(md_content):
    # Trouver la dernière occurrence de "Search"
    last_search_pos = md_content.rfind("Search")
    if last_search_pos != -1:
        # Supprimer tout avant et y compris "Search"
        md_content = md_content[last_search_pos + len("Search"):].strip()
    
    # Trouver l'occurrence de "## Vous pourriez aussi aimer ..."
    vous_aimer_pos = md_content.find("## Vous pourriez aussi aimer ...")
    if vous_aimer_pos != -1:
        # Supprimer tout après et y compris "## Vous pourriez aussi aimer ..."
        md_content = md_content[:vous_aimer_pos].strip()
    
    return md_content

# Sélectionner une page au hasard pour créer un fichier Markdown d'exemple
random_page_url, random_page_data = random.choice(list(scraped_data.items()))

# Dictionnaire pour stocker toutes les pages converties
converted_data = {}

# Parcourir toutes les pages du fichier scraped_data
for url, page_data in scraped_data.items():
    html_content = page_data['content']
    
    # Convertir avec markdownify
    markdown_text = convert_with_markdownify(html_content)
    markdown_text = clean_text(markdown_text)
    
    # Nettoyer le contenu markdown (retrait des menus et des suggestions à la fin)
    markdown_text_cleaned = clean_markdown_content(markdown_text)
    
    # Ajouter la page au dictionnaire converti
    converted_data[url] = {
        "title": page_data['title'],
        "url": url,
        "converted_markdown": markdown_text_cleaned
    }
    
    # Si c'est la page choisie au hasard, sauvegarder le fichier markdown sample
    if url == random_page_url:
        with open(markdown_output_file, 'w', encoding='utf-8') as md_file:
            md_file.write(f"# {page_data['title']}\n\n{markdown_text_cleaned}\n")

# Sauvegarder les résultats dans un fichier JSON structuré
with open(output_file, 'w', encoding='utf-8') as json_file:
    json.dump(converted_data, json_file, indent=4, ensure_ascii=False)

print(f"Conversion terminée. Les résultats sont sauvegardés dans {output_file} et un échantillon markdown dans {markdown_output_file}.")
