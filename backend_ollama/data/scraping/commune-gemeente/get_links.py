import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json
import os

# Set to store visited links to avoid duplicate visits
visited_links = set()

# Load previously saved links from the JSON file
def load_saved_links(filename='good_links.json'):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return set(json.load(f))  # Load as a set to quickly check for duplicates
    return set()

# Save the valid links into a JSON file
def save_to_json(data, filename='good_links.json'):
    with open(filename, 'w') as f:
        json.dump(list(data), f, indent=4)  # Convert set back to list for saving

# Function to check if the URL is an end link (i.e., contains actual information)
def is_valid_end_link(url):
    # Only consider links that end with .html and do not contain 'categorie'
    return url.endswith('.html') and 'categorie' not in url

# Function to recursively scrape useful links from a page
def scrape_links_recursively(base_url, current_url, saved_links):
    # Check if the URL has been visited
    if current_url in visited_links:
        return set()  # Return an empty set if already visited

    # Mark the URL as visited
    visited_links.add(current_url)

    # Fetch the page content
    try:
        response = requests.get(current_url)
        response.raise_for_status()  # Raise an exception for bad requests (4xx or 5xx)
    except requests.RequestException as e:
        print(f"Error fetching {current_url}: {e}")
        return set()

    soup = BeautifulSoup(response.content, 'html.parser')

    # Find all anchor tags
    links = soup.find_all('a', href=True)

    useful_links = set()

    # Iterate through the links to find valid end links
    for link in links:
        full_url = urljoin(base_url, link['href'])

        # Check if the link is an end link with useful information
        if is_valid_end_link(full_url) and full_url not in saved_links:
            useful_links.add(full_url)
        # Otherwise, if it's a valid link and not already visited, recursively follow it
        elif base_url in full_url and full_url not in visited_links:
            useful_links.update(scrape_links_recursively(base_url, full_url, saved_links))

    return useful_links

# Main scraping function
def main():
    base_url = 'https://www.commune-gemeente.be/'

    # Load previously saved links
    saved_links = load_saved_links()

    # Start recursive scraping from the base URL
    new_links = scrape_links_recursively(base_url, base_url, saved_links)

    # Combine newly found links with already saved ones
    all_links = saved_links.union(new_links)

    # Save the updated list of links
    save_to_json(all_links)

    print(f"Successfully saved {len(new_links)} new links and {len(all_links)} total links to 'good_links.json'.")

# Run the main function
if __name__ == '__main__':
    main()
