import requests
import json
import os
import random
from bs4 import BeautifulSoup
from markdownify import markdownify as md
import hashlib
from datetime import datetime

class ScrapingProgress:
    def __init__(self, output_dir):
        self.output_dir = output_dir
        self.successful_scrapes = 0
        self.failed_scrapes = 0
        self.duplicate_pages = 0
        self.start_time = datetime.now()
        
    def update_stats(self, success=False, duplicate=False):
        if duplicate:
            self.duplicate_pages += 1
        elif success:
            self.successful_scrapes += 1
        else:
            self.failed_scrapes += 1
            
    def save_progress(self):
        stats = {
            "successful_scrapes": self.successful_scrapes,
            "failed_scrapes": self.failed_scrapes,
            "duplicate_pages": self.duplicate_pages,
            "total_processed": self.successful_scrapes + self.failed_scrapes + self.duplicate_pages,
            "elapsed_time": str(datetime.now() - self.start_time)
        }
        
        stats_file = os.path.join(self.output_dir, 'scraping_stats.json')
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=4)
        
        print(f"\nCurrent Progress:")
        print(f"Successfully scraped: {self.successful_scrapes}")
        print(f"Failed scrapes: {self.failed_scrapes}")
        print(f"Duplicate pages: {self.duplicate_pages}")
        print(f"Time elapsed: {stats['elapsed_time']}\n")

def load_links(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f.readlines()]

def save_to_json(data, filename, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    filepath = os.path.join(output_dir, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def append_to_json(data, filename, output_dir):
    filepath = os.path.join(output_dir, filename)
    existing_data = {}
    
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
            
    existing_data.update(data)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=4)

def get_content_hash(content):
    return hashlib.md5(content.encode('utf-8')).hexdigest()

def fetch_page_data(url, processed_hashes, progress):
    base_url = "https://finances.belgium.be"
    full_url = base_url + url if not url.startswith('http') else url
    
    try:
        response = requests.get(full_url)
        
        if response.status_code == 404:
            print(f"404 Error: {full_url}")
            progress.update_stats(success=False)
            return None

        html_content = response.text
        content_hash = get_content_hash(html_content)
        
        if content_hash in processed_hashes:
            print(f"Duplicate page found, skipping: {full_url}")
            progress.update_stats(duplicate=True)
            return None
        processed_hashes.add(content_hash)

        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find the article element with the specific class
        main_content = soup.find('article', class_='node-page-full')
        if not main_content:
            print(f"No article content found in {full_url}")
            progress.update_stats(success=False)
            return None
            
        # Remove all img tags from the content
        for img_tag in main_content.find_all('img'):
            img_tag.decompose()
            
        # Get the title from the breadcrumb if available, otherwise use the article title
        title = soup.find('h1', class_='page-header')
        if title:
            title = title.get_text(strip=True)
        else:
            title = "No Title"

        progress.update_stats(success=True)
        return {
            "title": title,
            "content": str(main_content),
            "url": full_url
        }
    except requests.RequestException as e:
        print(f"Error fetching {full_url}: {e}")
        progress.update_stats(success=False)
        return None

def convert_to_markdown(html_data):
    return md(html_data)

def save_random_markdown_file(markdowns, output_dir):
    if not markdowns:
        print("No markdown data available to save random file")
        return
        
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    random_md_key = random.choice(list(markdowns.keys()))
    markdown_content = markdowns[random_md_key]['content']

    filename = random_md_key.split('/')[-1] + '.md'
    filepath = os.path.join(output_dir, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(markdown_content)

    print(f"Random markdown saved to {filepath}")

def scrape_pipeline(link_file, output_dir='output'):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    links = load_links(link_file)
    processed_hashes = set()
    progress = ScrapingProgress(output_dir)
    
    print(f"Starting to process {len(links)} links...")

    for i, link in enumerate(links, 1):
        print(f"\nProcessing link {i}/{len(links)}: {link}")
        
        # Step 1: Scrape page and extract article content
        page_data = fetch_page_data(link, processed_hashes, progress)
        if page_data:
            # Save raw HTML incrementally
            append_to_json({link: page_data}, 'raw_pages.json', output_dir)
            
            # Convert to markdown and save incrementally
            markdown_content = convert_to_markdown(page_data['content'])
            markdown_data = {
                link: {
                    "title": page_data["title"],
                    "content": markdown_content,
                    "url": page_data["url"]
                }
            }
            append_to_json(markdown_data, 'markdown_pages.json', output_dir)
        
        # Save progress after each page
        if i % 5 == 0 or i == len(links):  # Save stats every 5 pages and at the end
            progress.save_progress()

    # Final progress update
    progress.save_progress()
    
    # Save a random markdown file at the end
    try:
        with open(os.path.join(output_dir, 'markdown_pages.json'), 'r', encoding='utf-8') as f:
            all_markdowns = json.load(f)
            save_random_markdown_file(all_markdowns, output_dir)
    except FileNotFoundError:
        print("No markdown files were generated")

if __name__ == '__main__':
    link_file = 'content_links.txt'
    output_dir = 'belgium_gov_content'
    scrape_pipeline(link_file, output_dir)