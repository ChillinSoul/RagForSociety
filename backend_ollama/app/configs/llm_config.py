# app/configs/llm_config.py

from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langchain_community.llms import Ollama
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate

def create_llm_with_system_message(llm, system_message: str):
    """Helper function to create an LLM instance with a system message"""
    messages = [
        SystemMessagePromptTemplate.from_template(system_message),
        HumanMessagePromptTemplate.from_template("{input}")
    ]
    prompt = ChatPromptTemplate.from_messages(messages)
    return prompt | llm

# Different LLM configurations
CONFIGS = {
    "groq": {
        "llm_class": ChatGroq,
        "models": {
            "query_generator": "llama-3.2-90b-text-preview",
            "verifier": "llama-3.2-90b-text-preview",
            "precision_checker": "llama-3.2-90b-text-preview",
            "back_and_forth": "llama-3.2-90b-text-preview",
            "final": "llama-3.2-90b-text-preview",
            "multiple_choice": "llama-3.1-70b-versatile"
        }
    },
    "ollama-3.1": {
        "llm_class": ChatOllama,
        "models": {
            "query_generator": "llama3.1",
            "verifier": "llama3.1",
            "precision_checker": "llama3.1",
            "back_and_forth": "llama3.1",
            "final": "llama3.1",
            "multiple_choice": "llama3.1"
        }
    },
    "ollama-3.1-70b": {
        "llm_class": ChatOllama,
        "models": {
            "query_generator": "llama3.1:70b",
            "verifier": "llama3.1:70b",
            "precision_checker": "llama3.1:70b",
            "back_and_forth": "llama3.1:70b",
            "final": "llama3.1:70b",
            "multiple_choice": "llama3.1:70b"
        }
    },
    "ollama-hybrid": {
        "llm_class": ChatOllama,
        "models": {
            "query_generator": "llama3.1",
            "verifier": "llama3.1:70b",
            "precision_checker": "llama3.1:70b",
            "back_and_forth": "llama3.1",
            "final": "llama3.1:70b",
            "multiple_choice": "llama3.1:70b"
        }
    }
}

# Set the active configuration here
ACTIVE_CONFIG = "ollama-hybrid"

def get_llm(llm_type: str, system_message: str, temperature: float = 0):
    """Get an LLM instance based on the active configuration"""
    config = CONFIGS[ACTIVE_CONFIG]
    model_name = config["models"][llm_type]
    llm = config["llm_class"](
        model=model_name,
        temperature=temperature
    )
    return create_llm_with_system_message(llm, system_message)