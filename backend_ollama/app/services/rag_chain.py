from langchain.prompts import ChatPromptTemplate
from langchain_community.llms import Ollama
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda, RunnableMap, Runnable
from langchain_groq import ChatGroq
from operator import itemgetter
import logging

logger = logging.getLogger(__name__)

def initialize_rag_chain(
    retriever,
    use_verifier=True,
    automatic_verifier=False,
    llm_generate_queries=None,
    llm_verifier=None,
    llm_precision_checker=None,
    llm_back_and_forth=None,
    llm_final=None
):

    # Set default LLMs if not provided
    if llm_generate_queries is None:
        llm_generate_queries = ChatGroq(model="llama-3.2-90b-text-preview")

    if llm_verifier is None:
        llm_verifier = ChatGroq(model="llama-3.2-90b-text-preview")

    if llm_precision_checker is None:
        llm_precision_checker = ChatGroq(model="llama-3.2-90b-text-preview")

    if llm_back_and_forth is None:
        llm_back_and_forth = ChatGroq(model="llama-3.2-90b-text-preview")

    if llm_final is None:
        llm_final = ChatGroq(model="llama-3.2-90b-text-preview")

    #--------------------------- Retriever Verifier Chain --------------------------

    verifier_template = """
    Étant donné la question et le document suivants, déterminez si le document est un peu ou beaucoup lié à la question.
    Répondez "Oui" s'il est lié de près ou de loin, ou <non> s'il ne l'est pas. Ceci est dans le contexte des aides sociales en Belgique.
    Réfléchis avant de prendre la décision.

    Question : {question}

    Document : {document}

    Le document est-il lié de près ou de loin par rapport à la question ? Réfléchis en interne en plusieurs étapes concises, et ensuite répond par <oui> ou <non>. Si tu n'es pas sûr, répond <oui>.
    """

    verifier_prompt = ChatPromptTemplate.from_template(verifier_template)

    #--------------------------- Precision Checker Chain --------------------------

    precision_checker_template = """
    Étant donné la question suivante, déterminez si elle est suffisamment précise pour utiliser le vérificateur de documents en réfléchissant avant de prendre la décision.

    Question : {question}

    La question est-elle suffisamment précise pour utiliser le vérificateur de documents ?  Réfléchis en interne en plusieurs étapes concises, et ensuite répond par <oui> ou <non>. Si tu n'es pas sûr, répond <non>.
    """

    precision_checker_prompt = ChatPromptTemplate.from_template(precision_checker_template)

    # Define ConditionalVerifier Runnable
    class ConditionalVerifier(Runnable):
        def __init__(self, llm_verifier, llm_precision_checker, use_verifier=True, automatic_verifier=False):
            self.llm_verifier = llm_verifier
            self.llm_precision_checker = llm_precision_checker
            self.use_verifier = use_verifier
            self.automatic_verifier = automatic_verifier

        def invoke(self, inputs, config=None):
            question = inputs['question']
            retriever_results = inputs['retriever_results']

            if self.use_verifier:
                should_use_verifier = True
            elif self.automatic_verifier:
                # Use precision checker
                prompt_input = precision_checker_prompt.format(question=question)
                response = self.llm_precision_checker.invoke(prompt_input)
                logger.info(f"Precision Checker LLM response: {response.content}")
                should_use_verifier = '<oui>' in response.content or 'Oui' in response.content or 'oui' in response.content
            else:
                should_use_verifier = False

            if should_use_verifier:
                # Perform verification
                filtered_results = []
                for doc in retriever_results:
                    formatted_doc = doc.page_content if hasattr(doc, 'page_content') else doc.get('page_content', '')
                    prompt_input = verifier_prompt.format(question=question, document=formatted_doc)
                    response = self.llm_verifier.invoke(prompt_input)
                    logger.info(f"Verifier LLM response: {response.content}")
                    if '<oui>' in response.content or 'Oui' in response.content or 'oui' in response.content:
                        filtered_results.append(doc)
                retriever_results = filtered_results
                logger.info(f"Filtered results: {len(retriever_results)} documents after verification")
            else:
                logger.info("Verifier skipped based on precision checker or manual setting")

            return {
                'question': question,
                'retriever_results': retriever_results
            }

    # Create ConditionalVerifier instance
    conditional_verifier = ConditionalVerifier(
        llm_verifier=llm_verifier,
        llm_precision_checker=llm_precision_checker,
        use_verifier=use_verifier,
        automatic_verifier=automatic_verifier
    )

    #------------------------------ Multi Query Retrieval Chain --------------------------------------

    multi_query_template = """Vous êtes un assistant modèle de langage IA.
    Votre tâche est de générer cinq versions différentes de la question posée par l'utilisateur
    afin de récupérer des documents pertinents à partir d'une base de données vectorielle dans le domaine des **aides sociales en Belgique**.
    En générant plusieurs perspectives de la question de l'utilisateur avec un peu plus de recul,
    votre objectif est d'aider l'utilisateur à surmonter certaines des limites de la recherche de similarité basée sur la distance.
    Fournissez ces questions alternatives, séparées par des sauts de ligne. Ne rends que les questions sans texte supplémentaire.
    Question originale : {question}"""

    prompt_perspectives = ChatPromptTemplate.from_template(multi_query_template)

    generate_queries = (
        prompt_perspectives
        | llm_generate_queries
        | StrOutputParser()
        | RunnableLambda(lambda x: [query.strip() for query in x.split("\n") if query.strip()])
    )

    # Updated reciprocal_rank_fusion function
    def reciprocal_rank_fusion(results: list[list], k=60):
        fused_scores = {}
        for docs in results:
            for rank, doc in enumerate(docs):
                # Use the document's content and metadata as a key to ensure uniqueness
                doc_key = (doc.page_content, tuple(sorted(doc.metadata.items())) if doc.metadata else None)
                if doc_key not in fused_scores:
                    fused_scores[doc_key] = {'score': 0, 'doc': doc}
                fused_scores[doc_key]['score'] += 1 / (rank + k)

        # Sort documents by fused score
        reranked_results = sorted(fused_scores.values(), key=lambda x: x['score'], reverse=True)
        # Extract documents
        reranked_docs = [entry['doc'] for entry in reranked_results]
        logger.info(f"Reranked results length: {len(reranked_docs)}")
        return reranked_docs[:5]

    # Wrap reciprocal_rank_fusion in RunnableLambda
    reciprocal_rank_fusion_runnable = RunnableLambda(reciprocal_rank_fusion)

    # Adjusted retrieval_chain to pass question along with the results
    retrieval_chain = (
        RunnableMap({'question': lambda x: x})
        | RunnableMap({
            'question': itemgetter('question'),
            'queries': generate_queries
        })
        | RunnableLambda(lambda inputs: {
            'question': inputs['question'],
            'retriever_results_list': retriever.map().invoke(inputs['queries'])
        })
        | RunnableLambda(lambda inputs: {
            'question': inputs['question'],
            'retriever_results': reciprocal_rank_fusion(inputs['retriever_results_list'])
        })
        | conditional_verifier  # Use the ConditionalVerifier here
    )

    #---------------------------- Back and forth chain ---------------------------

    back_and_forth_template = """Tu es un assistant IA qui aide un utilisateur à poser une question plus précise.
    Tu as besoin de reformuler la question de l'utilisateur pour obtenir une réponse plus précise.
    Tu as accès à un questionnaire rempli par l'utilisateur pour t'aider à reformuler la question.
    Tu as accès à des documents pertinents pour t'aider à reformuler la question.

    Documents : {context}

    Question : {question}

    Questionnaire : {questionaire}

    Reformule la question de l'utilisateur pour obtenir une réponse plus précise.
    """

    back_and_forth_prompt = ChatPromptTemplate.from_template(back_and_forth_template)

    generate_query_back_and_forth = (
        back_and_forth_prompt
        | llm_back_and_forth
        | StrOutputParser()
    )

    def format_docs(docs):
        formatted_docs = []
        for doc in docs:
            if isinstance(doc, tuple) and len(doc) == 2:
                document, score = doc
                content = document.page_content if hasattr(document, 'page_content') else document.get('page_content', '')
                formatted_docs.append(content)
            elif isinstance(doc, dict):
                formatted_docs.append(doc.get('page_content', ''))
            elif hasattr(doc, 'page_content'):
                formatted_docs.append(doc.page_content)
            else:
                formatted_docs.append(str(doc))
        return "\n\n".join(formatted_docs)

    def get_context(data):
        return format_docs(data["retriever_results"])

    #--------------------------- Main Chain ---------------------------------

    template = """Tu es une IA qui a pour objectif d'aider des personnes à trouver s'ils peuvent toucher des aides sociales.
    Réponds aux questions selon le contexte et donne des **explications concises**.
    Si tu n'as pas de réponse, ou bien qu'il n'y a rien dans le contexte dis-le !
    Si tu as besoin que l'auteur reformule la question, aide-le en proposant plusieurs choix, mais ne réponds pas qu'avec les liens, donne des explications dans ta réponse.
    Si le contexte te procure un lien utile, écris-le dans ta réponse au **format Markdown**.
    **Écris ta réponse dans le format Markdown**.
    Réponds à la question uniquement en te basant sur le contexte suivant :
    {context}

    Question : {question}
    """

    prompt = ChatPromptTemplate.from_template(template)

    final_chain = (
        RunnableMap({
            "context": get_context,
            "question": itemgetter("question")
        })
        | prompt
        | llm_final
        | StrOutputParser()
    )

    logger.info("RAG chain initialized successfully")
    return retrieval_chain, final_chain, generate_query_back_and_forth
