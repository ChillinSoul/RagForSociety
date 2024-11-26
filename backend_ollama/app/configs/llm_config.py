from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate

def create_llm_with_system_message(llm, system_message: str):
    """Helper function to create an LLM instance with a system message"""
    messages = [
        SystemMessagePromptTemplate.from_template(system_message),
        HumanMessagePromptTemplate.from_template("{input}")
    ]
    prompt = ChatPromptTemplate.from_messages(messages)
    return prompt | llm

CONFIGS = {
    "groq": {  # Recommended for best performance/cost ratio
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
    "chatgpt": {  # Alternative cloud option
        "llm_class": ChatOpenAI,
        "models": {
            "query_generator": "gpt-4o-mini",
            "verifier": "gpt-4o-mini",
            "precision_checker": "gpt-4o-mini",
            "back_and_forth": "gpt-4o-mini",
            "final": "gpt-4o-mini",
            "multiple_choice": "gpt-4o-mini"
        }
    },
    "ollama-3.1": {  # Lightweight local configuration
        "llm_class": ChatOllama,
        "models": {
            "query_generator": "llama2:8b",
            "verifier": "llama2:8b",
            "precision_checker": "llama2:8b",
            "back_and_forth": "llama2:8b",
            "final": "llama2:8b",
            "multiple_choice": "llama2:8b"
        }
    },
    "ollama-3.1-70b": {  # Full local configuration
        "llm_class": ChatOllama,
        "models": {
            "query_generator": "llama2:70b",
            "verifier": "llama2:70b",
            "precision_checker": "llama2:70b",
            "back_and_forth": "llama2:70b",
            "final": "llama2:70b",
            "multiple_choice": "llama2:70b"
        }
    },
    "ollama-hybrid": {  # Balanced local configuration
        "llm_class": ChatOllama,
        "models": {
            "query_generator": "llama2:8b",
            "verifier": "llama2:8b",
            "precision_checker": "llama2:70b",
            "back_and_forth": "llama2:8b",
            "final": "llama2:70b",
            "multiple_choice": "llama2:70b"
        }
    }
}

# Set the active configuration here
ACTIVE_CONFIG = "chatgpt"  # Recommended for best performance

def get_llm(llm_type: str, system_message: str, temperature: float = 0):
    """Get an LLM instance based on the active configuration"""
    config = CONFIGS[ACTIVE_CONFIG]
    model_name = config["models"][llm_type]
    llm = config["llm_class"](
        model=model_name,
        temperature=temperature
    )
    return create_llm_with_system_message(llm, system_message)