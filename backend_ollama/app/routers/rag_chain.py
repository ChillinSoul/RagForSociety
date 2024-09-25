from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from app.models import QuestionRequest
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

retrieval_chain = None
final_chain = None

def initialize_rag_chain_global(retrieval, final):
    global retrieval_chain, final_chain
    retrieval_chain = retrieval
    final_chain = final

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
    else:
        return str(doc)

@router.post("/get-response/")
async def get_response(request: QuestionRequest):
    global retrieval_chain, final_chain
    try:
        if retrieval_chain is None or final_chain is None:
            logger.error("RAG chain not initialized")
            raise HTTPException(status_code=500, detail="RAG chain not initialized")
        
        question = request.question
        logger.info(f"Received question: {question}")
        
        # Get retriever results
        retrieval_results = retrieval_chain.invoke(question)
        serialized_results = [serialize_document(doc) for doc in retrieval_results]
        logger.info(f"Retrieval results: {serialized_results}")
        
        # Get LLM response
        llm_response = final_chain.invoke({"question": question, "retriever_results": retrieval_results})
        logger.info(f"LLM response: {llm_response}")
        
        # Combine the retriever results and the LLM response
        combined_response = {
            "retriever_results": serialized_results,
            "llm_response": llm_response
        }
        
        logger.info(f"Sent combined response: {combined_response}")
        return JSONResponse(content=combined_response)
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")