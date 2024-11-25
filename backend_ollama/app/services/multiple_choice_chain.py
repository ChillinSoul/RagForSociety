# app/services/multiple_choice_chain.py

from app.configs.prompts import create_prompt_templates
from langchain.chains import LLMChain
from langchain.output_parsers import PydanticOutputParser
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field, ValidationError
import logging

logger = logging.getLogger(__name__)

def initialize_multiple_choice_chain():
    """
    Initializes a multiple-choice question generation chain using LangChain tools.
    Generates JSON-based multiple-choice questions about user characteristics.
    """

    # Define the Pydantic model for the expected output
    class Question(BaseModel):
        text: str = Field(..., description="The question text")
        options: list[str] = Field(..., description="List of options, the last one should be 'N/A'")

    class MCQuestions(BaseModel):
        questions: list[Question]

    # Initialize the output parser
    output_parser = PydanticOutputParser(pydantic_object=MCQuestions)

    # Get prompt templates
    prompts = create_prompt_templates()
    mc_prompt = prompts["mc_prompt"]

    # Initialize the LLM
    llm = ChatGroq(
        model="llama-3.1-70b-versatile",
        temperature=0.7
    )
    
    # Define the chain
    mc_chain = LLMChain(
        llm=llm,
        prompt=mc_prompt
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
        logger.info(f"Extracted question: {repr(question)}")
        context = get_mc_context(data)

        try:
            # Use the invoke method
            response = mc_chain.invoke({
                "context": context,
                "question": question
            })
            logger.info(f"LLMChain response: {response}")

            # Extract the generated text from the response
            if isinstance(response, dict) and 'text' in response:
                generated_text = response['text']
            else:
                # Handle ChatGroq response format
                content = response.content if hasattr(response, 'content') else str(response)
                generated_text = content

            if not generated_text:
                logger.error("No text output from LLM.")
                return {}

            # Try to parse the generated text
            parsed_response = output_parser.parse(generated_text)
            return parsed_response.model_dump()

        except ValidationError as e:
            logger.error(f"Failed to parse multiple-choice response: {str(e)}")
            return {}

        except Exception as e:
            logger.error(f"Error during LLM call: {str(e)}")
            logger.error(f"Response was: {response}")
            return {}

    logger.info("Multiple-choice chain with JSON output initialized successfully")
    return run_mc_chain