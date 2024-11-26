from app.configs.prompts import create_prompt_templates, SYSTEM_MESSAGES
from app.configs.llm_config import get_llm
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field, ValidationError
import logging
from typing import List
import json

logger = logging.getLogger(__name__)

# Define the Pydantic models at module level
class Question(BaseModel):
    text: str = Field(..., description="The question text")
    options: List[str] = Field(..., description="List of options, the last one should be 'N/A'")

class MCQuestions(BaseModel):
    questions: List[Question]

def initialize_multiple_choice_chain():
    """
    Initializes a multiple-choice question generation chain using LangChain tools.
    Generates JSON-based multiple-choice questions about user characteristics.
    """
    # Initialize the output parser
    output_parser = PydanticOutputParser(pydantic_object=MCQuestions)

    # Get prompts from config
    prompts = create_prompt_templates()

    # Get LLM with system message
    llm = get_llm(
        llm_type="multiple_choice",
        system_message=SYSTEM_MESSAGES["multiple_choice"],
        temperature=0.7
    )

    def format_docs(docs: list, max_chars: int = 2000) -> str:
        """
        Formats retrieved documents by truncating them and preparing them for inclusion in the context.
        Includes source URLs for each document.
        """
        formatted_docs = []
        for i, doc in enumerate(docs):
            if i > 2:  # Limit to first 3 documents
                break
                
            # Extract content and URL based on document type
            if hasattr(doc, 'page_content'):
                content = doc.page_content
                url = doc.metadata.get('url', 'No URL available') if hasattr(doc, 'metadata') else 'No URL available'
            elif isinstance(doc, dict):
                content = doc.get('page_content', '')
                url = doc.get('metadata', {}).get('url', 'No URL available')
            else:
                content = str(doc)
                url = 'No URL available'
            
            # Format document with URL
            formatted_doc = f"""Source: {url}
---
{content[:max_chars]}
---"""
            formatted_docs.append(formatted_doc)
            
        return "\n\n".join(formatted_docs)

    def get_mc_context(data: dict) -> str:
        """
        Extracts and formats the context from the retrieved documents.
        """
        return format_docs(data.get("retriever_results", []))

    def run_mc_chain(data: dict) -> dict:
        """
        Runs the multiple-choice question generation chain, ensuring the correct context and question.
        """
        logger.info("Running multiple-choice chain with JSON output")

        if "question" not in data:
            logger.error('The key "question" is missing from data.')
            raise ValueError('The key "question" is missing from data.')

        question = data["question"].strip()
        # logger.info(f"Extracted question: {repr(question)}")
        context = get_mc_context(data)

        try:
            # Use the prompt template from config
            formatted_prompt = prompts["mc_prompt"].format(
                context=context,
                question=question
            )
            
            # Call the LLM
            llm_response = llm.invoke({"input": formatted_prompt})
            # logger.info(f"Raw LLM response: {llm_response}")

            # Extract the content from the response
            if hasattr(llm_response, 'content'):
                response_text = llm_response.content
            else:
                response_text = str(llm_response)

            # logger.info(f"Extracted response text: {response_text}")

            # Clean the response text to ensure it's valid JSON
            response_text = response_text.strip()
            if response_text.startswith('```json'):
                response_text = response_text.replace('```json', '', 1)
            if response_text.endswith('```'):
                response_text = response_text.rsplit('```', 1)[0]
            response_text = response_text.strip()

            # Parse the JSON response
            parsed_response = output_parser.parse(response_text)
            result = parsed_response.model_dump()
            # logger.info(f"Successfully parsed response: {result}")
            return result

        except ValidationError as e:
            logger.error(f"Failed to parse multiple-choice response: {str(e)}")
            return {"questions": []}

        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON response: {str(e)}")
            return {"questions": []}

        except Exception as e:
            logger.error(f"Error during LLM call: {str(e)}")
            logger.error(f"Response was: {locals().get('llm_response', 'No response available')}")
            return {"questions": []}

    logger.info("Multiple-choice chain with JSON output initialized successfully")
    return run_mc_chain