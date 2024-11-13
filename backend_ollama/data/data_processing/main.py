import getpass
import json
import os
from dotenv import load_dotenv
from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain_groq import ChatGroq


load_dotenv(".env")

os.environ['LANGCHAIN_TRACING_V2'] = 'true'
os.environ['LANGCHAIN_ENDPOINT'] = 'https://api.smith.langchain.com'
# Retrieve the API key from the .env file
os.environ['LANGCHAIN_API_KEY'] = os.getenv('LANGCHAIN_API_KEY')

if "GROQ_API_KEY" not in os.environ:
    os.environ["GROQ_API_KEY"] = getpass.getpass("Enter your Groq API key: ")

# Initialize the Ollama model
# llm = Ollama(model="llama3.1")

llm = ChatGroq( model="llama-3.2-11b-text-preview")

# Create a prompt template for summarizing content
prompt_template = PromptTemplate(
    input_variables=["content"],
    template="Écris un résumé pour ce texte dans le contexte de fournir le plus d'informations possible sur un certain sujet à un utilisateur. Le résumé doit contenir toutes les informations du document mais d'une façon structurée et plus courte **Écris seulement le résumé, pas de texte en plus (par exemple:N'écris pas de \"Voici un résumé structuré du texte:\")**: {content}"
)

# Initialize a RunnableSequence (replacing the LLMChain)
summarize_chain = prompt_template | llm

def process_and_summarize(data, output_file):
    total_items = len(data)
    for i, item in enumerate(data):
        # Skip items that are already summarized
        if "summarized" in item and item["summarized"] == True:
            continue

        print(f"Processing item {i+1}/{total_items}")
        # Summarize the content array
        summarized_content = []
        string = " ".join(item["content"])
        if item["conditions"] != []:
            string += " conditions: " + " ".join(item["conditions"])
        if item["table_rows"] != []:
            string += " table data: " + " ".join(item["table_rows"])

        # Invoke the summarization (directly get the result as a string)
        summary = summarize_chain.invoke({"content": string})
        print(f"Summarized: {summary}")

        summarized_content.append(summary)

        # Replace original content with summarized content
        item["content"] = summarized_content
        item["summarized"] = True  # Mark the item as summarized

        # Save after processing each item
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    return data

def load_data(output_file, input_file):
    # If summarized data file exists, load it, otherwise load the original data
    if os.path.exists(output_file):
        print(f"Resuming from {output_file}...")
        with open(output_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        print(f"Starting fresh from {input_file}...")
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    return data

def main():
    input_file = "output.json"
    output_file = "summarized_data_test_basil_0.json"

    # Load data (resume if output file exists)
    data = load_data(output_file, input_file)

    # Process and summarize the JSON content
    summarized_data = process_and_summarize(data, output_file)

if __name__ == "__main__":
    main()
