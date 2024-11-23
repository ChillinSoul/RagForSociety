import requests
from bs4 import BeautifulSoup
import urllib.parse
import time

# Base URLs
base_url = "https://finances.belgium.be"
sitemap_url = "https://finances.belgium.be/fr/sitemap"

def has_content(url):
    """Check if the page has actual content by looking for non-empty <p> in <main>"""
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        main = soup.find('main')
        if main:
            # Find all paragraphs
            paragraphs = main.find_all('p')
            # Check if any paragraph has actual content (not just whitespace or &nbsp;)
            for p in paragraphs:
                # Get text and remove whitespace
                text = p.get_text().strip()
                # Skip if empty or just &nbsp;
                if text and text != '\xa0':
                    return True
        return False
    except:
        return False

def save_link(url, filename="content_links.txt"):
    """Save a single link to the file"""
    with open(filename, "a") as file:
        file.write(f"{url}\n")

def extract_links():
    """Extract links from sitemap and check each for content"""
    print("Starting extraction from sitemap...")
    
    # Get the sitemap page
    response = requests.get(sitemap_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find all links in the menu structure
    processed = set()
    count = 0
    
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        
        # Make sure URL is complete
        full_url = urllib.parse.urljoin(base_url, href)
        
        # Skip if already processed or external link
        if full_url in processed or base_url not in full_url:
            continue
            
        processed.add(full_url)
        
        # Check if it's a content page
        if has_content(full_url):
            save_link(full_url)
            count += 1
            print(f"Found content page ({count}): {full_url}")
        
        # Add delay between requests
        time.sleep(1)
    
    print(f"Extraction complete. Found {count} content pages.")

if __name__ == "__main__":
    # Clear the file before starting
    open("content_links.txt", "w").close()
    
    # Start extraction
    extract_links()