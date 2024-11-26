from typing import Dict, Any, Tuple
from app.configs.prompts import SYSTEM_MESSAGES, create_prompt_templates
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda, RunnableMap, Runnable
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from operator import itemgetter
from app.configs.prompts import SYSTEM_MESSAGES
from app.configs.llm_config import get_llm
import logging
import tiktoken

logger = logging.getLogger(__name__)

class TokenCounter:
    def __init__(self):
        self.reset()
        logger.info("TokenCounter initialized")
    
    def reset(self):
        self.token_counts = {
            "prompt_tokens": 0,
            "completion_tokens": 0
        }
        logger.info("TokenCounter reset")
    
    def on_llm_start(self, input_text: str):
        token_count = count_tokens(input_text)
        self.token_counts["prompt_tokens"] += token_count
        logger.info(f"Added {token_count} prompt tokens. New total: {self.token_counts['prompt_tokens']}")
    
    def on_llm_end(self, output_text: str):
        token_count = count_tokens(output_text)
        self.token_counts["completion_tokens"] += token_count
        logger.info(f"Added {token_count} completion tokens. New total: {self.token_counts['completion_tokens']}")
    
    def get_counts(self):
        total = sum(self.token_counts.values())
        counts = {
            "prompt_tokens": self.token_counts["prompt_tokens"],
            "completion_tokens": self.token_counts["completion_tokens"],
            "total_tokens": total
        }
        logger.info(f"Current token counts: {counts}")
        return counts

def count_tokens(text: str) -> int:
    """Count tokens in text using tiktoken"""
    try:
        encoding = tiktoken.get_encoding("cl100k_base")
        token_count = len(encoding.encode(str(text)))
        logger.info(f"Counted {token_count} tokens for text of length {len(str(text))}")
        return token_count
    except Exception as e:
        logger.error(f"Error counting tokens: {e}")
        return 0

def create_llm_with_system_message(model_name: str, system_message: str, temperature: float = 0):
    """Helper function to create a ChatGroq instance with a system message"""
    messages = [
        SystemMessagePromptTemplate.from_template(system_message),
        HumanMessagePromptTemplate.from_template("{input}")
    ]
    prompt = ChatPromptTemplate.from_messages(messages)
    
    llm = ChatGroq(
        model=model_name,
        temperature=temperature,
    )
    
    return prompt | llm

def initialize_rag_chain(
    retriever,
    use_verifier=True,
    automatic_verifier=False,
) -> Tuple[Runnable, Runnable, Runnable, TokenCounter]:
    token_counter = TokenCounter()
    
    # Get all prompt templates
    prompts = create_prompt_templates()

    # Set default LLMs if not provided
    llm_generate_queries = get_llm("query_generator", SYSTEM_MESSAGES["query_generator"], temperature=0.9)
    llm_verifier = get_llm("verifier", SYSTEM_MESSAGES["verifier"])
    llm_precision_checker = get_llm("precision_checker", SYSTEM_MESSAGES["precision_checker"])
    llm_back_and_forth = get_llm("back_and_forth", SYSTEM_MESSAGES["back_and_forth"])
    llm_final = get_llm("final", SYSTEM_MESSAGES["final_response"])

    def count_tokens_wrapper(chain):
        def wrapped(input_data):
            input_str = str(input_data)
            token_counter.on_llm_start(input_str)
            result = chain.invoke(input_data)
            token_counter.on_llm_end(str(result))
            return result
        return wrapped

    class ConditionalVerifier(Runnable):
        def __init__(self, llm_verifier, llm_precision_checker, use_verifier=True, automatic_verifier=False):
            self.llm_verifier = llm_verifier
            self.llm_precision_checker = llm_precision_checker
            self.use_verifier = use_verifier
            self.automatic_verifier = automatic_verifier
            self.prompts = create_prompt_templates()

        def invoke(self, inputs, config=None):
            question = inputs['question']
            retriever_results = inputs['retriever_results']

            if self.use_verifier:
                should_use_verifier = True
            elif self.automatic_verifier:
                # Count tokens and use precision checker
                token_counter.on_llm_start(str(question))
                response = self.llm_precision_checker.invoke(
                    {"input": self.prompts["precision_checker_prompt"].format(question=question)}
                )
                token_counter.on_llm_end(str(response))
                should_use_verifier = '<oui>' in response
                logger.info(f"Precision checker response: {response}")
            else:
                should_use_verifier = False

            if should_use_verifier:
                logger.info("Running verifier")
                filtered_results = []
                for doc in retriever_results:
                    formatted_doc = doc.page_content if hasattr(doc, 'page_content') else doc.get('page_content', '')
                    
                    # Count tokens for verification
                    token_counter.on_llm_start(str(formatted_doc))
                    response = self.llm_verifier.invoke(
                        {"input": self.prompts["verifier_prompt"].format(
                            question=question,
                            document=formatted_doc
                        )}
                    )
                    token_counter.on_llm_end(str(response))
                    
                    response = response.content if hasattr(response, 'content') else str(response)
                    if '<oui>' in response:
                        logger.info("Verifier accepted document")
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

    generate_queries = (
        RunnableLambda(lambda x: {"input": prompts["multi_query_prompt"].format(question=x)})
        | RunnableLambda(count_tokens_wrapper(llm_generate_queries))
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
        return reranked_docs[:5]

    reciprocal_rank_fusion_runnable = RunnableLambda(reciprocal_rank_fusion)

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
                url = document.metadata.get('url', 'No URL available') if hasattr(document, 'metadata') else 'No URL available'
            elif isinstance(doc, dict):
                content = doc.get('page_content', '')
                url = doc.get('metadata', {}).get('url', 'No URL available')
            elif hasattr(doc, 'page_content'):
                content = doc.page_content
                url = doc.metadata.get('url', 'No URL available') if hasattr(doc, 'metadata') else 'No URL available'
            else:
                content = str(doc)
                url = 'No URL available'
            
            formatted_doc = f"""Source: {url}\n---\n{content}\n---"""
            formatted_docs.append(formatted_doc)
        
        return "\n\n".join(formatted_docs)

    def get_context(data):
        return format_docs(data["retriever_results"])

    generate_query_back_and_forth = (
        RunnableLambda(lambda x: {"input": prompts["back_and_forth_prompt"].format(**x)})
        | RunnableLambda(count_tokens_wrapper(llm_back_and_forth))
        | StrOutputParser()
    )

    final_chain = (
        RunnableMap({
            "context": get_context,
            "question": itemgetter("question")
        })
        | RunnableLambda(lambda x: {"input": prompts["final_response_prompt"].format(**x)})
        | RunnableLambda(count_tokens_wrapper(llm_final))
        | StrOutputParser()
    )

    logger.info("RAG chain initialized successfully")
    return retrieval_chain, final_chain, generate_query_back_and_forth, token_counter