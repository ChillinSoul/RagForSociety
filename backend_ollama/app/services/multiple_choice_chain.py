from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.chains import LLMChain
from langchain.output_parsers import PydanticOutputParser
from langchain_community.llms import Ollama
from langchain_openai import ChatOpenAI
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

    # Define the prompt templates
    system_template = """
    Tu es un assistant qui génère des questions à choix multiples sous forme de JSON pour obtenir des informations précises et personnelles sur l'utilisateur.
    Les questions doivent porter sur les **caractéristiques personnelles, habitudes, préférences, besoins** ou **situations spécifiques** de l'utilisateur, et être basées sur le contexte fourni.
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

    Répond uniquement en **JSON** et sans aucun texte additionnel.
    """

    human_template = """
    Documents : {context}

    Question initiale : {question}
    """

    system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)
    human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

    mc_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])

    # Initialize the LLM
    llm = Ollama(model="llama3.1")
    #llm = ChatOpenAI(model="gpt-3.5-turbo-0125")
    #llm = ChatGroq( model="llama-3.2-11b-text-preview")
    # Define the chain without the output_parser
    mc_chain = LLMChain(
        llm=llm,
        prompt=mc_prompt
        # Remove output_parser
    )

    def format_docs(docs: list, max_chars: int = 2000) -> str:
        """
        Formats retrieved documents by truncating them and preparing them for inclusion in the context.
        """
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
            response = mc_chain.invoke({"context": context, "question": question})
            logger.info(f"LLMChain response: {response}")

            generated_text = response.get('text', '')
            if not generated_text:
                logger.error("No text output from LLM.")
                return {}

            # Manually parse the output
            parsed_response = output_parser.parse(generated_text)
            return parsed_response.model_dump()

        except ValidationError as e:
            logger.error(f"Failed to parse multiple-choice response: {str(e)}")
            return {}

        except Exception as e:
            logger.error(f"Error during LLM call: {str(e)}")
            return {}

    logger.info("Multiple-choice chain with JSON output initialized successfully")
    return run_mc_chain