# app/services/rag_chain.py
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_community.llms import Ollama
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda, RunnableMap, Runnable
from langchain_groq import ChatGroq
from operator import itemgetter
import logging

logger = logging.getLogger(__name__)

def initialize_rag_chain(
    retriever,
    config_service,
    use_verifier=True,
    automatic_verifier=False,
    experiment_group: str = "baseline"
):
    logger.info(f"Initializing RAG chain with experiment group: {experiment_group}")

    # Get model configurations from database with experiment group
    multi_query_config = config_service.get_model_config("multi_query", experiment_group)
    verifier_config = config_service.get_model_config("verifier", experiment_group)
    final_config = config_service.get_model_config("final_answer", experiment_group)

    if not all([multi_query_config, verifier_config, final_config]):
        logger.warning("Some configurations not found, falling back to defaults")
        if not multi_query_config:
            multi_query_config = {"name": "llama-3.2-90b-text-preview", "parameters": {"temperature": 0.9}}
        if not verifier_config:
            verifier_config = {"name": "llama-3.2-90b-text-preview", "parameters": {"temperature": 0.1}}
        if not final_config:
            final_config = {"name": "llama-3.2-90b-text-preview", "parameters": {"temperature": 0.1}}

    # Initialize LLMs with configurations from database
    llm_generate_queries = ChatGroq(
        model=multi_query_config["name"],
        **multi_query_config.get("parameters", {})
    )
    
    llm_verifier = ChatGroq(
        model=verifier_config["name"],
        **verifier_config.get("parameters", {})
    )
    
    llm_final = ChatGroq(
        model=final_config["name"],
        **final_config.get("parameters", {})
    )

    # Get prompt templates from database and combine with system prompts
    multi_query_template = config_service.get_prompt_template("multi_query")
    if multi_query_config.get("system_prompt"):
        system_message = SystemMessagePromptTemplate.from_template(multi_query_config["system_prompt"])
        human_message = HumanMessagePromptTemplate.from_template(multi_query_template)
        prompt_perspectives = ChatPromptTemplate.from_messages([system_message, human_message])
    else:
        prompt_perspectives = ChatPromptTemplate.from_template(multi_query_template)

    verifier_template = config_service.get_prompt_template("verifier")
    if verifier_config.get("system_prompt"):
        system_message = SystemMessagePromptTemplate.from_template(verifier_config["system_prompt"])
        human_message = HumanMessagePromptTemplate.from_template(verifier_template)
        verifier_prompt = ChatPromptTemplate.from_messages([system_message, human_message])
    else:
        verifier_prompt = ChatPromptTemplate.from_template(verifier_template)

    final_template = config_service.get_prompt_template("final_answer")
    if final_config.get("system_prompt"):
        system_message = SystemMessagePromptTemplate.from_template(final_config["system_prompt"])
        human_message = HumanMessagePromptTemplate.from_template(final_template)
        final_prompt = ChatPromptTemplate.from_messages([system_message, human_message])
    else:
        final_prompt = ChatPromptTemplate.from_template(final_template)

    if not all([multi_query_template, verifier_template, final_template]):
        raise ValueError("Required prompt templates not found in database")

    generate_queries = (
        prompt_perspectives
        | llm_generate_queries
        | StrOutputParser()
        | RunnableLambda(lambda x: [query.strip() for query in x.split("\n") if query.strip()])
    )

    def reciprocal_rank_fusion(results: list[list], k=60):
        fused_scores = {}
        for docs in results:
            for rank, doc in enumerate(docs):
                doc_key = (doc.page_content, tuple(sorted(doc.metadata.items())) if doc.metadata else None)
                if doc_key not in fused_scores:
                    fused_scores[doc_key] = {'score': 0, 'doc': doc}
                fused_scores[doc_key]['score'] += 1 / (rank + k)

        reranked_results = sorted(fused_scores.values(), key=lambda x: x['score'], reverse=True)
        reranked_docs = [entry['doc'] for entry in reranked_results]
        logger.info(f"Reranked results length: {len(reranked_docs)}")
        return reranked_docs[:10]

    reciprocal_rank_fusion_runnable = RunnableLambda(reciprocal_rank_fusion)

    class ConditionalVerifier(Runnable):
        def __init__(self, llm_verifier, use_verifier=True, automatic_verifier=False):
            self.llm_verifier = llm_verifier
            self.use_verifier = use_verifier
            self.automatic_verifier = automatic_verifier

        def invoke(self, inputs, config=None):
            question = inputs['question']
            retriever_results = inputs['retriever_results']

            if self.use_verifier:
                filtered_results = []
                for doc in retriever_results:
                    formatted_doc = doc.page_content if hasattr(doc, 'page_content') else doc.get('page_content', '')
                    prompt_input = {"question": question, "document": formatted_doc}
                    response = self.llm_verifier.invoke(verifier_prompt.format_messages(**prompt_input))
                    logger.info(f"Verifier LLM response: {response.content}")
                    if '<oui>' in response.content or 'Oui' in response.content or 'oui' in response.content:
                        filtered_results.append(doc)
                retriever_results = filtered_results
                logger.info(f"Filtered results: {len(retriever_results)} documents after verification")
            else:
                logger.info("Verifier skipped based on settings")

            return {
                'question': question,
                'retriever_results': retriever_results
            }

    conditional_verifier = ConditionalVerifier(
        llm_verifier=llm_verifier,
        use_verifier=use_verifier,
        automatic_verifier=automatic_verifier
    )

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
        | conditional_verifier
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

    final_chain = (
        RunnableMap({
            "context": get_context,
            "question": itemgetter("question")
        })
        | final_prompt
        | llm_final
        | StrOutputParser()
    )

    logger.info("RAG chain initialized successfully")
    return retrieval_chain, final_chain, None