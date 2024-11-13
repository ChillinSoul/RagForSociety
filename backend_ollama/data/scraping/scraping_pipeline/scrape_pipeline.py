import requests
import json
import os
import random
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from difflib import SequenceMatcher
import hashlib

# Function to load a list of URLs from a file
def load_links(filename):
    with open(filename, 'r') as f:
        return [line.strip() for line in f.readlines()]

# Function to save data to a JSON file
def save_to_json(data, filename, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)  # Create the directory if it doesn't exist
    filepath = os.path.join(output_dir, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# Function to calculate the hash of a webpage's content
def get_content_hash(content):
    return hashlib.md5(content.encode('utf-8')).hexdigest()

# Function to fetch raw HTML content, ignore 404 pages, and remove all images
def fetch_page_data(url, processed_hashes):
    try:
        response = requests.get(url)
        
        # Skip if the page returns a 404 or other errors
        if response.status_code == 404:
            print(f"404 Error: {url}")
            return None

        # Get the raw HTML content
        html_content = response.text
        
        # Calculate the hash of the content to detect duplicates
        content_hash = get_content_hash(html_content)
        if content_hash in processed_hashes:
            print(f"Duplicate page found, skipping: {url}")
            return None
        processed_hashes.add(content_hash)

        # Parse the HTML content and remove all <img> tags
        soup = BeautifulSoup(html_content, 'html.parser')
        for img_tag in soup.find_all('img'):
            img_tag.decompose()

        # Extract the title of the page
        title = soup.title.string if soup.title else "No Title"

        return {
            "title": title,
            "content": str(soup),
            "url": url
        }
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

# Function to convert HTML content to markdown
def convert_to_markdown(html_data):
    return md(html_data)

# Function to clean redundant start/end sections from markdowns
def clean_redundant_sections(markdowns):
    markdowns_list = list(markdowns.items())
    random.shuffle(markdowns_list)
    cleaned_markdowns = {}

    for i in range(0, len(markdowns_list) - 1, 2):
        url1, md1 = markdowns_list[i]
        url2, md2 = markdowns_list[i + 1]

        cleaned_md1 = clean_redundant_parts(md1['content'], md2['content'])
        cleaned_md2 = clean_redundant_parts(md2['content'], md1['content'])

        cleaned_markdowns[url1] = {"title": md1["title"], "content": cleaned_md1, "url": md1["url"]}
        cleaned_markdowns[url2] = {"title": md2["title"], "content": cleaned_md2, "url": md2["url"]}

    return cleaned_markdowns

# Helper function to clean redundant parts using sequence matching
def clean_redundant_parts(markdown1, markdown2):
    matcher_start = SequenceMatcher(None, markdown1, markdown2)
    match_start = matcher_start.find_longest_match(0, len(markdown1), 0, len(markdown2))

    if match_start.size > 20:
        cleaned_markdown = markdown1[match_start.size:]
    else:
        cleaned_markdown = markdown1

    return cleaned_markdown

# Function to save a random markdown as a .md file
def save_random_markdown_file(markdowns, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    random_md_key = random.choice(list(markdowns.keys()))
    markdown_content = markdowns[random_md_key]['content']

    filename = random_md_key.split('/')[-1].replace('.html', '.md')
    filepath = os.path.join(output_dir, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(markdown_content)

    print(f"Random markdown saved to {filepath}")

# Main pipeline function to scrape, convert, clean, and save markdown
def scrape_pipeline(link_file, output_dir='output'):
    # Load the list of links
    links = load_links(link_file)

    # Set to track hashes of page content to avoid duplicates
    processed_hashes = set()

    # Step 1: Scrape pages and remove images, ignoring 404 and duplicates
    raw_data = {}
    for link in links:
        page_data = fetch_page_data(link, processed_hashes)
        if page_data:
            raw_data[link] = page_data

    # Save raw HTML data to a JSON file
    save_to_json(raw_data, 'raw_pages.json', output_dir)

    # Step 2: Convert HTML to markdown and save to a new JSON
    markdown_data = {}
    for url, page_data in raw_data.items():
        markdown_content = convert_to_markdown(page_data['content'])
        markdown_data[url] = {
            "title": page_data["title"],
            "content": markdown_content,
            "url": page_data["url"]
        }
    
    save_to_json(markdown_data, 'markdown_pages.json', output_dir)

    # Step 3: Clean redundant sections from markdowns
    cleaned_markdown_data = clean_redundant_sections(markdown_data)
    
    save_to_json(cleaned_markdown_data, 'cleaned_markdown_pages.json', output_dir)

    # Step 4: Randomly save one markdown as a .md file
    save_random_markdown_file(cleaned_markdown_data, output_dir)

if __name__ == '__main__':
    # Specify the input file containing the list of links to scrape
    link_file = 'unique_links.txt'  # Modify this with your link file

    # Specify the output directory where all files should be saved
    output_dir = 'sécurité_sociale'  # Modify this to your desired output directory

    # Run the pipeline
    scrape_pipeline(link_file, output_dir)
