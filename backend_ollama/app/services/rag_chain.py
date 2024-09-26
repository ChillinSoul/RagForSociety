from langchain.prompts import ChatPromptTemplate
from langchain_community.llms import Ollama
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain.load import dumps, loads
from operator import itemgetter
import logging

logger = logging.getLogger(__name__)

def initialize_rag_chain(retriever):
    template = """soit concis. Si tu n'as pas de reponse dit le.
      Si tu as besoins que l'auteur reformule la question, aide le en proposant plusieur choix.
      Répond à la question uniquement en te basant sur le contexte suivant:
    {context}

    Question : {question}
    """

    prompt = ChatPromptTemplate.from_template(template)
    llm = Ollama(model="llama3.1")

    multi_query_template = """Vous êtes un assistant modèle de langage IA. 
    Votre tâche est de générer cinq versions différentes de la question posée par l'utilisateur 
    afin de récupérer des documents pertinents à partir d'une base de données vectorielle. 
    En générant plusieurs perspectives de la question de l'utilisateur, 
    votre objectif est d'aider l'utilisateur à surmonter certaines des limites de la recherche de similarité basée sur la distance. 
    Fournissez ces questions alternatives, séparées par des sauts de ligne. ne rends que les quetions sans text supplémentaire.
    Question originale : {question}"""
    prompt_perspectives = ChatPromptTemplate.from_template(multi_query_template)

    def log_llm_message(message):
        logger.info(f"Message sent to LLM: {message}")
        return message

    generate_queries = (
        prompt_perspectives 
        | log_llm_message
        | llm 
        | StrOutputParser() 
        | (lambda x: x.split("\n"))
    )

    def reciprocal_rank_fusion(results: list[list], k=60):
        fused_scores = {}
        for docs in results:
            for rank, doc in enumerate(docs):
                doc_str = dumps(doc)
                if doc_str not in fused_scores:
                    fused_scores[doc_str] = 0
                fused_scores[doc_str] += 1 / (rank + k)

        reranked_results = [
            (loads(doc), score)
            for doc, score in sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)
        ]

        return reranked_results

    retrieval_chain = generate_queries | retriever.map() | reciprocal_rank_fusion

    def format_docs(docs):
        formatted_docs = []
        for doc in docs:
            if isinstance(doc, tuple) and len(doc) == 2:
                document, score = doc
                content = document.page_content if hasattr(document, 'page_content') else document.get('page_content', '')
                formatted_docs.append(content)
            elif isinstance(doc, dict):
                formatted_docs.append(doc.get('page_content', ''))
            else:
                formatted_docs.append(str(doc))
        return "\n\n".join(formatted_docs)

    def get_context(data):
        return format_docs(data["retriever_results"])

    final_chain = (
        {
            "context": get_context, 
            "question": itemgetter("question")
        }
        | prompt
        | log_llm_message
        | llm
        | StrOutputParser()
    )

    logger.info("RAG chain initialized successfully")
    return retrieval_chain, final_chain