from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from app.models import QuestionRequest, QuestionBackAndForthRequest, TokenCount
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

retrieval_chain = None
final_chain = None
mc_chain = None
generate_query_back_and_forth = None
token_counter = None

def initialize_rag_chain_global(retrieval, final, mc, back_and_forth, counter):
    global retrieval_chain, final_chain, mc_chain, generate_query_back_and_forth, token_counter
    retrieval_chain = retrieval
    final_chain = final
    mc_chain = mc
    generate_query_back_and_forth = back_and_forth
    token_counter = counter

def serialize_document(doc):
    if hasattr(doc, 'to_dict'):
        return doc.to_dict()
    elif isinstance(doc, tuple) and len(doc) == 2:
        document, score = doc
        return {
            "page_content": document.page_content,
            "metadata": document.metadata,
            "score": score
        }
    elif hasattr(doc, 'page_content') and hasattr(doc, 'metadata'):
        return {
            "page_content": doc.page_content,
            "metadata": doc.metadata
        }
    else:
        logger.warning(f"Unexpected document format: {doc}")
        return str(doc)
    
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

@router.post("/get-response/")
async def get_response(request: QuestionRequest):
    global retrieval_chain, final_chain, mc_chain, token_counter
    try:
        if not all([retrieval_chain, final_chain, mc_chain, token_counter]):
            logger.error("RAG chain not initialized")
            logger.error(f"retrieval_chain: {retrieval_chain is not None}")
            logger.error(f"final_chain: {final_chain is not None}")
            logger.error(f"mc_chain: {mc_chain is not None}")
            logger.error(f"token_counter: {token_counter is not None}")
            raise HTTPException(status_code=500, detail="RAG chain not initialized")
        
        logger.info("Starting new request processing")
        token_counter.reset()
        question = request.question.strip()
        logger.info(f"Processing question: {question}")

        # Get retriever results
        retrieval_output = retrieval_chain.invoke(question)
        retrieval_results = retrieval_output['retriever_results']
        serialized_results = [serialize_document(doc) for doc in retrieval_results]
        logger.info(f"Retrieved {len(serialized_results)} documents")

        # Get LLM response
        llm_response = final_chain.invoke({"question": question, "retriever_results": retrieval_results})
        logger.info("Generated LLM response")

        # Get multiple-choice response
        mc_response = mc_chain({"question": question, "retriever_results": retrieval_results})
        logger.info("Generated MC response")
        
        # Get token counts
        token_counts = token_counter.get_counts()
        logger.info(f"Final token counts for request: {token_counts}")
        
        combined_response = {
            "retriever_results": serialized_results,
            "llm_response": llm_response,
            "mc_response": mc_response,
            "token_counts": token_counts
        }
        
        logger.info("Sending response with token counts")
        return JSONResponse(content=combined_response)
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@router.post("/get-response-bnf/")
async def get_response_back_and_forth(request: QuestionBackAndForthRequest):
    global generate_query_back_and_forth, retrieval_chain, final_chain, token_counter
    try:
        if not all([generate_query_back_and_forth, retrieval_chain, final_chain, token_counter]):
            logger.error("Back-and-forth chain not initialized")
            raise HTTPException(status_code=500, detail="Back-and-forth chain not initialized")
        
        token_counter.reset()  # Reset token counter for new request
        question = request.question.strip()
        questionaire_data = request.questionaire or []
        questionaire = " ".join(f"{item['question']} {item['reponse']} ." for item in questionaire_data)

        retrieval_output = retrieval_chain.invoke(question)
        context_docs = retrieval_output['retriever_results']
        
        context_string = format_docs(context_docs)
        
        enhanced_query = generate_query_back_and_forth.invoke({
            "question": question,
            "questionaire": questionaire,
            "context": context_string
        })
        
        retrieval_output = retrieval_chain.invoke(enhanced_query)
        retrieval_results = retrieval_output['retriever_results']
        serialized_results = [serialize_document(doc) for doc in retrieval_results]
        
        llm_response = final_chain.invoke({
            "question": enhanced_query,
            "retriever_results": retrieval_results
        })

        token_counts = token_counter.get_counts()

        combined_response = {
            "retriever_results": serialized_results,
            "llm_response": llm_response,
            "mc_response": [],
            "token_counts": token_counts
        }

        return JSONResponse(content=combined_response)

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")