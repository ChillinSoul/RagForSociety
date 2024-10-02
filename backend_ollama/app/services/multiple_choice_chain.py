from langchain.prompts import ChatPromptTemplate
from langchain_community.llms import Ollama
from langchain_groq import ChatGroq
import json
import re
import logging

logger = logging.getLogger(__name__)

def initialize_multiple_choice_chain():
    """
    Initializes a multiple-choice question generation chain using a refined prompt template.
    Generates JSON-based multiple-choice questions about user characteristics.
    """
    mc_template = """
    Génère des questions à choix multiples sous forme de JSON pour obtenir des informations précises et personnelles sur l'utilisateur.
    Les questions doivent porter sur les **caractéristiques personnelles, habitudes, préférences, besoins** ou **situations spécifiques** **pas de question sur la conaissance** de l'utilisateur, et être basées sur le contexte fourni.
    Chaque question doit être directement liée à l'utilisateur, concise, et proposer 3 à 4 options de réponse pertinentes. **La dernière option doit toujours être "N/A"**.
    Le format du JSON doit être **strictement respecté** comme suit, sans explication supplémentaire ou texte non formaté :

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
        }},
        {{
          "text": "Autre question sur l'utilisateur ici",
          "options": [
            "Option A",
            "Option B",
            "Option C",
            "N/A"
          ]
        }}
      ]
    }}

    Les questions doivent se concentrer sur les informations manquantes concernant l'utilisateur. Répond uniquement en **JSON** et sans aucun texte additionnel.

    Documents : {context}

    Question initiale : {question}
"""
    
    mc_prompt = ChatPromptTemplate.from_template(mc_template)
    # llm = Ollama(model="llama3.1")
    # llm = ChatGroq(model="llama-3.2-90b-text-preview")
    llm = ChatGroq(model="llama-3.1-70b-versatile")

    def parse_mc_response(mc_response: str) -> dict:
        """
        Parses the response from the LLM, cleaning the JSON and returning the parsed result.
        """
        try:
            if not mc_response.strip():
                logger.error("LLM returned an empty response.")
                return []
            
            logger.info(f"Raw LLM response: {mc_response}")
            mc_response = mc_response[mc_response.find('{'):mc_response.rfind('}')+1]
            cleaned_response = mc_response.strip().replace('\n', '').replace('\/\"', '"')
            cleaned_response = re.sub(r'\\(?![/u"])', '', cleaned_response)
            cleaned_response = re.sub(r'\s*,\s*', ', ', cleaned_response)
            parsed_response = json.loads(cleaned_response)

            if isinstance(parsed_response, dict) and "questions" in parsed_response:
                return parsed_response
            else:
                logger.error(f"Parsed response does not match expected format: {parsed_response}")
                return []

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse multiple-choice response: {str(e)}")
            return []

    def generate_mc_questions(context: str, question: str) -> dict:
        """
        Generates multiple-choice questions by calling the LLM with a formatted prompt.
        """
        sanitized_context = context.strip() if isinstance(context, str) else context
        sanitized_question = question.strip()

        try:
            formatted_prompt = mc_prompt.format(context=sanitized_context, question=sanitized_question)
            mc_response = llm.invoke(formatted_prompt)

            return parse_mc_response(mc_response)

        except Exception as e:
            logger.error(f"Error during LLM call: {str(e)}")
            return []

    def format_docs(docs: list, max_chars: int = 2000) -> str:
        """
        Formats retrieved documents by truncating them and preparing them for inclusion in the context.
        """
        formatted_docs = []
        for i, doc in enumerate(docs):
            if i > 2:
                break
            if isinstance(doc, tuple) and len(doc) == 2:
                document, score = doc
                content = document.page_content if hasattr(document, 'page_content') else document.get('page_content', '')
                formatted_docs.append(content[:max_chars])
            elif isinstance(doc, dict):
                formatted_docs.append(doc.get('page_content', '')[:max_chars])
            else:
                formatted_docs.append(str(doc)[:max_chars])
        return "\n\n".join(formatted_docs)

    def get_mc_context(data: dict) -> str:
        """
        Extracts and formats the context from the retrieved documents.
        """
        return format_docs(data["retriever_results"])

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
        return generate_mc_questions(context, question)

    logger.info("Multiple-choice chain with JSON output initialized successfully")
    return run_mc_chain