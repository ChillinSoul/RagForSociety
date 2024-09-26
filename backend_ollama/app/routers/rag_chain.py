from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from app.models import QuestionRequest
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

retrieval_chain = None
final_chain = None
mc_chain = None

def initialize_rag_chain_global(retrieval, final, mc):
    global retrieval_chain, final_chain, mc_chain
    retrieval_chain = retrieval
    final_chain = final
    mc_chain = mc

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
    global retrieval_chain, final_chain, mc_chain
    try:
        if retrieval_chain is None or final_chain is None or mc_chain is None:
            logger.error("RAG chain not initialized")
            raise HTTPException(status_code=500, detail="RAG chain not initialized")
        
        question = request.question.strip()  # Clean up the question to remove any unwanted newlines or spaces
        logger.info(f"Received question: {repr(question)}")  # Log the raw question with special characters
        
        # Get retriever results (using invoke method)
        retrieval_results = retrieval_chain.invoke(question)
        serialized_results = [serialize_document(doc) for doc in retrieval_results]
        # logger.info(f"Retrieval results: {serialized_results[:500]} ...")
        
        # Get LLM response (using invoke method)
        llm_response = final_chain.invoke({"question": question, "retriever_results": retrieval_results})
        logger.info(f"LLM response: {llm_response}")

        # Get multiple-choice response (assuming mc_chain is callable directly)
        logger.info("Running multiple-choice chain")
        mc_response = mc_chain({"question": question, "retriever_results": retrieval_results})
        logger.info(f"Multiple-choice response: {mc_response}")
        
        # Combine the retriever results, LLM response, and multiple-choice response
        combined_response = {
            "retriever_results": serialized_results,
            "llm_response": llm_response,
            "mc_response": mc_response
        }
        
        logger.info(f"Sent combined response:")# {combined_response}")
        return JSONResponse(content=combined_response)
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")