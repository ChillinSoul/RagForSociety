# app/routers/rag_chain.py
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from app.models import QuestionRequest, QuestionBackAndForthRequest
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

retrieval_chain = None
final_chain = None
mc_chain = None
generate_query_back_and_forth = None
config_service = None

def initialize_rag_chain_global(retrieval, final, mc, back_and_forth, config):
    global retrieval_chain, final_chain, mc_chain, generate_query_back_and_forth, config_service
    retrieval_chain = retrieval
    final_chain = final
    mc_chain = mc
    generate_query_back_and_forth = back_and_forth
    config_service = config

def serialize_document(doc):
    logger.info(f"Serializing document of type {type(doc)}: {doc}")
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
    global retrieval_chain, final_chain, mc_chain, config_service
    try:
        if retrieval_chain is None or final_chain is None or mc_chain is None:
            logger.error("RAG chain not initialized")
            raise HTTPException(status_code=500, detail="RAG chain not initialized")
        
        question = request.question.strip()
        logger.info(f"Received question: {repr(question)}")

        retrieval_output = retrieval_chain.invoke(question)
        retrieval_results = retrieval_output['retriever_results']
        serialized_results = [serialize_document(doc) for doc in retrieval_results]

        llm_response = final_chain.invoke({"question": question, "retriever_results": retrieval_results})
        logger.info(f"LLM response: {llm_response}")

        logger.info("Running multiple-choice chain")
        mc_response = mc_chain({"question": question, "retriever_results": retrieval_results})
        logger.info(f"Multiple-choice response: {mc_response}")
        
        combined_response = {
            "retriever_results": serialized_results,
            "llm_response": llm_response,
            "mc_response": mc_response
        }
        
        logger.info(f"Sent combined response")
        return JSONResponse(content=combined_response)
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")