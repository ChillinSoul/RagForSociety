import requests
from bs4 import BeautifulSoup
import time
import json
import os

base_url = "https://aide-sociale.be/"
visited = set()  # Ensemble des liens déjà visités
output_file = "scraped_data.json"
links_file = "links_to_scrape.json"
scraped_links_file = "scraped_links.json"

# Charger les données déjà scrapees si le fichier existe
if os.path.exists(output_file):
    with open(output_file, 'r') as file:
        scraped_data = json.load(file)
else:
    scraped_data = {}

# Charger les liens déjà scrape si le fichier existe
if os.path.exists(scraped_links_file):
    with open(scraped_links_file, 'r') as file:
        scraped_links = set(json.load(file))
else:
    scraped_links = set()

# Sauvegarder les données scrapees dans un fichier JSON
def save_scraped_data(data):
    with open(output_file, 'w') as file:
        json.dump(data, file, indent=4)

# Sauvegarder la liste des liens à scraper dans un fichier JSON
def save_links(links):
    with open(links_file, 'w') as file:
        json.dump(links, file, indent=4)

# Sauvegarder les liens déjà scrape dans un fichier JSON
def save_scraped_links(links):
    with open(scraped_links_file, 'w') as file:
        json.dump(list(links), file, indent=4)

# Fonction pour récupérer les liens des sections à partir de la barre de navigation
def get_links_from_navbar(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Trouver les liens des menus principaux
    nav_links = []
    for nav_item in soup.select('nav a[href]'):
        href = nav_item['href']
        if href.startswith('/') or href.startswith(base_url):
            full_url = base_url + href[1:] if href.startswith('/') else href
            if full_url not in visited and full_url not in scraped_data:
                nav_links.append(full_url)
                visited.add(full_url)
    
    return nav_links

# Fonction pour récupérer les sous-pages des sections, par exemple, les cartes avec des liens d'articles
def get_subpages(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Trouver les liens sur les cartes avec les images
    subpage_links = []
    for card in soup.select('article a[href]'):
        href = card['href']
        if href.startswith('/') or href.startswith(base_url):
            full_url = base_url + href[1:] if href.startswith('/') else href
            if full_url not in visited and full_url not in scraped_data:
                subpage_links.append(full_url)
                visited.add(full_url)
    
    return subpage_links

# Fonction pour scraper les pages finales
def scrape_final_pages(links, max_pages=5):
    scraped_count = 0
    for link in links:
        if scraped_count >= max_pages:
            break
        if link in scraped_links:  # Ne pas scraper les liens déjà traités
            continue

        print(f"Scraping {link}...")
        try:
            response = requests.get(link)
            response.raise_for_status()  # S'assurer qu'il n'y a pas d'erreur HTTP
            page_html = response.text  # Obtenir tout le HTML brut

            # Extraire le titre (facultatif, mais utile pour référence)
            soup = BeautifulSoup(page_html, 'html.parser')
            title = soup.find('title').text if soup.find('title') else 'No title'

            # Sauvegarde dans le fichier JSON
            scraped_data[link] = {
                "title": title,
                "content": page_html,  # Sauvegarde tout le HTML brut
                "url": link
            }

            # Sauvegarder les liens déjà scrape
            scraped_links.add(link)
            save_scraped_links(scraped_links)

            # Sauvegarder après chaque page
            save_scraped_data(scraped_data)
            scraped_count += 1

            time.sleep(1)  # Pause pour éviter de surcharger le serveur
        except Exception as e:
            print(f"Erreur lors du scraping de {link}: {e}")

# Fonction principale pour scraper les données
def main():
    # Si le fichier de liens existe, on le charge, sinon on les génère
    if os.path.exists(links_file):
        with open(links_file, 'r') as file:
            all_final_links = json.load(file)
    else:
        # Étape 1: Explorer la navbar
        nav_links = get_links_from_navbar(base_url)
        
        # Étape 2: Explorer chaque section et trouver les sous-pages
        all_final_links = []
        for section_link in nav_links:
            print(f"Exploring section {section_link}...")
            subpage_links = get_subpages(section_link)
            all_final_links.extend(subpage_links)
        
        # Sauvegarder les liens dans un fichier pour éviter de les regénérer
        save_links(all_final_links)

    # Étape 3: Scraper les pages finales, limité à 5 pages pour le test
    scrape_final_pages(all_final_links, max_pages=200)

if __name__ == "__main__":
    main()
