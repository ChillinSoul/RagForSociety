import requests
import json
import os
import random
from markdownify import markdownify as md
from difflib import SequenceMatcher

# Load saved links from the JSON file
def load_json(filename):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

# Save the data into a JSON file
def save_to_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# Convert HTML content to Markdown
def convert_to_markdown(html_data):
    return md(html_data)

# Function to clean redundant start/end sections from markdowns
def clean_redundant_sections(markdowns):
    # Sort markdowns randomly for comparison
    markdowns_list = list(markdowns.items())
    random.shuffle(markdowns_list)

    cleaned_markdowns = {}

    # Iterate through markdowns pairwise to compare
    for i in range(0, len(markdowns_list) - 1, 2):
        url1, md1 = markdowns_list[i]
        url2, md2 = markdowns_list[i + 1]

        cleaned_md1 = clean_redundant_parts(md1['content'], md2['content'])
        cleaned_md2 = clean_redundant_parts(md2['content'], md1['content'])

        # Save the cleaned markdowns in the same format
        cleaned_markdowns[url1] = {"title": md1["title"], "content": cleaned_md1, "url": md1["url"]}
        cleaned_markdowns[url2] = {"title": md2["title"], "content": cleaned_md2, "url": md2["url"]}

    return cleaned_markdowns

# Helper function to find and remove redundant sections from the start and end
def clean_redundant_parts(markdown1, markdown2):
    matcher_start = SequenceMatcher(None, markdown1, markdown2)
    match_start = matcher_start.find_longest_match(0, len(markdown1), 0, len(markdown2))

    # Remove similar starting and ending sections
    if match_start.size > 20:  # Threshold to consider similarity
        cleaned_markdown = markdown1[match_start.size:]
    else:
        cleaned_markdown = markdown1

    return cleaned_markdown

# Function to randomly select and save one of the markdowns as a .md file
def save_random_markdown_file(markdowns, output_dir='markdown_files'):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    random_md_key = random.choice(list(markdowns.keys()))
    markdown_content = markdowns[random_md_key]['content']

    filename = random_md_key.split('/')[-1].replace('.html', '.md')
    filepath = os.path.join(output_dir, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(markdown_content)

    print(f"Random markdown saved to {filepath}")

# Main function
def main():
    # Load the raw HTML data
    raw_data = load_json('french_pages.json')

    # Step 1: Convert HTML to Markdown and save to a new JSON
    markdown_data = {}
    for url, page_data in raw_data.items():
        markdown_content = convert_to_markdown(page_data['content'])
        markdown_data[url] = {
            "title": page_data["title"],
            "content": markdown_content,
            "url": page_data["url"]
        }
    
    # Save the markdown data to a JSON file
    save_to_json(markdown_data, 'markdown_pages.json')

    # Step 2: Clean redundant sections from the markdowns
    cleaned_markdown_data = clean_redundant_sections(markdown_data)

    # Save the cleaned markdowns to a new JSON file
    save_to_json(cleaned_markdown_data, 'cleaned_markdown_pages.json')

    # Step 3: Randomly select a cleaned markdown and save as a .md file
    save_random_markdown_file(cleaned_markdown_data)

if __name__ == '__main__':
    main()
