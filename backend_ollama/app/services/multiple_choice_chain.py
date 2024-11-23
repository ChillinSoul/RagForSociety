# app/services/multiple_choice_chain.py
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_groq import ChatGroq
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from pydantic import BaseModel, Field
import json
import logging

logger = logging.getLogger(__name__)

def initialize_multiple_choice_chain(config_service=None, experiment_group: str = "baseline"):
    """Initialize multiple choice chain with configuration from database."""
    logger.info(f"Initializing multiple-choice chain with experiment group: {experiment_group}")

    class Question(BaseModel):
        text: str = Field(..., description="The question text")
        options: list[str] = Field(..., description="List of options, the last one should be 'N/A'")

    class MCQuestions(BaseModel):
        questions: list[Question]

    output_parser = PydanticOutputParser(pydantic_object=MCQuestions)

    JSON_FORMAT_INSTRUCTIONS = '''
Réponds uniquement avec un JSON au format suivant:
{{
  "questions": [
    {{
      "text": "Question sur l'utilisateur ici",
      "options": [
        "Option 1",
        "Option 2",
        "Option 3",
        "N/A"
      ]
    }}
  ]
}}'''

    # Initialize the LLM with configuration from database if available
    if config_service:
        mc_config = config_service.get_model_config("multiple_choice", experiment_group)
        template = config_service.get_prompt_template("multiple_choice")
        
        if mc_config:
            logger.info("Using database configuration for multiple choice model")
            llm = ChatGroq(
                model=mc_config["name"],
                **mc_config.get("parameters", {})
            )
        else:
            logger.warning("No multiple_choice configuration found, using default")
            llm = ChatGroq(model="llama-3.1-70b-versatile")
    else:
        logger.warning("No config_service provided, using default configuration")
        llm = ChatGroq(model="llama-3.1-70b-versatile")
        template = f"""Tu es un assistant qui génère des questions à choix multiples.
        
Documents : {{context}}

Question initiale : {{question}}

{JSON_FORMAT_INSTRUCTIONS}"""

    # Create the prompt template with system message if available
    if config_service and mc_config and mc_config.get("system_prompt"):
        system_template = f"{mc_config['system_prompt']}\n{JSON_FORMAT_INSTRUCTIONS}"
        system_message = SystemMessagePromptTemplate.from_template(system_template)
        human_message = HumanMessagePromptTemplate.from_template(template)
        chat_prompt = ChatPromptTemplate.from_messages([system_message, human_message])
    else:
        chat_prompt = ChatPromptTemplate.from_messages([
            HumanMessagePromptTemplate.from_template(template)
        ])

    def format_docs(docs: list, max_chars: int = 2000) -> str:
        formatted_docs = []
        for i, doc in enumerate(docs):
            if i > 2:
                break
            if hasattr(doc, 'page_content'):
                content = doc.page_content
            elif isinstance(doc, dict):
                content = doc.get('page_content', '')
            else:
                content = str(doc)
            formatted_docs.append(content[:max_chars])
        return "\n\n".join(formatted_docs)

    def get_mc_context(data: dict) -> str:
        return format_docs(data.get("retriever_results", []))

    def parse_llm_output(output) -> str:
        """Parse LLM output and ensure it returns a JSON string"""
        try:
            # If we got an AI message object, get its content
            if hasattr(output, 'content'):
                output = output.content

            # Try to parse the output as JSON to validate it
            parsed = json.loads(output)
            
            # If we got a list instead of a dict with questions key
            if isinstance(parsed, list):
                parsed = {"questions": parsed}
            
            # Return the formatted JSON string
            return json.dumps(parsed)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from LLM output: {e}")
            return json.dumps({"questions": []})
        except Exception as e:
            logger.error(f"Unexpected error parsing LLM output: {e}")
            return json.dumps({"questions": []})

    def run_mc_chain(data: dict) -> dict:
        logger.info("Running multiple-choice chain with JSON output")

        if "question" not in data:
            logger.error('The key "question" is missing from data.')
            raise ValueError('The key "question" is missing from data.')

        try:
            chain = (
                RunnablePassthrough() 
                | {"context": get_mc_context, "question": lambda x: x["question"]}
                | chat_prompt 
                | llm 
                | RunnableLambda(parse_llm_output)  # Convert to JSON string
                | output_parser  # Parse JSON string to Pydantic model
            )
            
            response = chain.invoke(data)
            logger.info(f"Chain response: {response}")
            return response.model_dump()

        except Exception as e:
            logger.error(f"Error during chain execution: {str(e)}")
            return {"questions": []}

    logger.info("Multiple-choice chain initialized successfully")
    return run_mc_chain