import requests
from bs4 import BeautifulSoup
import urllib.parse

# The base URL to start scraping from
base_url = "https://www.socialsecurity.be/citizen/fr"

# Function to extract all links from a page
def extract_links(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    links = []
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        # Ensure the link is fully qualified
        full_url = urllib.parse.urljoin(url, href)
        # Skip external links
        if base_url in full_url:
            links.append(full_url)
    return links

# Recursive function to explore each link
def explore_links(url, depth, max_depth, visited, all_links):
    if depth > max_depth or url in visited:
        return
    
    visited.add(url)
    
    # Extract links from the current page
    links = extract_links(url)
    
    # Add new links to the set of all links
    all_links.update(links)
    
    for link in links:
        explore_links(link, depth + 1, max_depth, visited, all_links)

# Main function
def main():
    visited = set()
    all_links = set()  # Use a set to automatically handle duplicates
    
    # Explore the base URL
    explore_links(base_url, depth=0, max_depth=5, visited=visited, all_links=all_links)
    
    # Write the unique links to a text file
    with open("unique_links.txt", "w") as file:
        for link in sorted(all_links):
            file.write(f"{link}\n")
    
    print("Extraction complete. Check unique_links.txt for the result.")

if __name__ == "__main__":
    main()
