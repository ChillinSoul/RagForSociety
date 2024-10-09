import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.routers import scraped_data, rag_chain
from app.services.data_loader import load_documents
from app.services.vectorstore import initialize_vectorstore
from app.services.rag_chain import initialize_rag_chain
from app.services.multiple_choice_chain import initialize_multiple_choice_chain
import logging
import getpass
import os

load_dotenv(".env")

os.environ['LANGCHAIN_TRACING_V2'] = 'true'
os.environ['LANGCHAIN_ENDPOINT'] = 'https://api.smith.langchain.com'
# Retrieve the API key from the .env file
os.environ['LANGCHAIN_API_KEY'] = os.getenv('LANGCHAIN_API_KEY')

if "GROQ_API_KEY" not in os.environ:
    os.environ["GROQ_API_KEY"] = getpass.getpass("Enter your Groq API key: ")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:3000", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    try:
        logger.info("Initializing application...")
        file_path = os.environ.get("FILE_PATH", "new_output.json")
        logger.info(f"Loading documents from {file_path}")
        docs = load_documents(file_path)
        logger.info(f"Loaded {len(docs)} documents")
        
        logger.info("Initializing vectorstore")
        vectorstore = initialize_vectorstore(docs)
        
        logger.info("Creating retriever")
        retriever = vectorstore.as_retriever()
        # search_kwargs={"k": 1}
        
        logger.info("Initializing RAG chain")
        retrieval_chain, final_chain, generate_query_back_and_forth = initialize_rag_chain(retriever)
        mc_chain = initialize_multiple_choice_chain()
        rag_chain.initialize_rag_chain_global(retrieval_chain, final_chain, mc_chain, generate_query_back_and_forth)
        logger.info("Application initialized successfully")
    except Exception as e:
        logger.error(f"Error during initialization: {str(e)}")
        raise

app.include_router(scraped_data.router)
app.include_router(rag_chain.router)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTPException: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred."}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)