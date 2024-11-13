import requests
from bs4 import BeautifulSoup
import json
import os

# Load saved links from the JSON file
def load_saved_links(filename='good_links.json'):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)  # Load as a list
    return []

# Function to filter out only French links (those containing '/fr/')
def filter_french_links(links):
    return [link for link in links if '/fr/' in link]

# Function to fetch raw HTML content and extract title
def fetch_page_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Ensure the request was successful
        html_content = response.text  # Get the raw HTML content
        
        # Parse the HTML to extract the title
        soup = BeautifulSoup(html_content, 'html.parser')
        title = soup.title.string if soup.title else "No Title"

        # Return a dictionary with the title, content, and URL
        return {
            "title": title,
            "content": html_content,
            "url": url
        }
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

# Function to save the full dataset to a JSON file
def save_to_json(data, filename='french_pages.json'):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# Main function to load links, filter French ones, and save their raw HTML in an organized JSON structure
def main():
    # Load previously saved links
    saved_links = load_saved_links()

    # Filter only French links
    french_links = filter_french_links(saved_links)

    print(f"Found {len(french_links)} French links.")

    # Dictionary to hold the full dataset for the JSON output
    page_data = {}

    # Fetch and save raw HTML content for each French link
    for link in french_links:
        data = fetch_page_data(link)
        if data:
            page_data[link] = data

    # Save the entire data set to a JSON file
    save_to_json(page_data)

    print(f"Successfully saved the page data to 'french_pages.json'.")

# Run the main function
if __name__ == '__main__':
    main()
