import json

from langchain_community.llms import Ollama
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

# Initialize the Ollama model
llm = Ollama(model="llama3.1")

# Create a prompt template for summarizing content
prompt_template = PromptTemplate(
    input_variables=["content"],
    template="Summarize the following content extrat all important information **don't add extra text just output the summary**: {content}"
)

# Initialize LLM chain
summarize_chain = LLMChain(llm=llm, prompt=prompt_template)

def process_and_summarize(data):
    # Extract and summarize the content from JSON
    total_items = len(data)
    for i,item in enumerate(data):
        print(f"Processing item {i+1}/{total_items}")
        # Summarize the content array
        summarized_content = []
        string = " ".join(item["content"])
        if item["conditions"] != []:
            string += "conditions: " + " ".join(item["conditions"])
        if item["table_rows"] != []:
            string += "table data: " + " ".join(item["table_rows"])
        summary = summarize_chain.run(content=string)
        summarized_content.append(summary)
        
        # Replace original content with summarized content
        item["content"] = summarized_content
    
    return data

def main():
    # Load your JSON data
    with open("output.json", "r") as f:
        data = json.load(f)

    # Process and summarize the JSON content
    summarized_data = process_and_summarize(data)

    # Save the summarized JSON data
    with open("summarized_data.json", "w") as f:
        json.dump(summarized_data, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()