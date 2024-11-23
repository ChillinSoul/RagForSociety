# app/main.py
import io
import os
import uuid
from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
import getpass

from app.routers import scraped_data, rag_chain, speech, experiments
from app.services.data_loader import load_documents
from app.services.vectorstore import initialize_vectorstore
from app.services.rag_chain import initialize_rag_chain
from app.services.multiple_choice_chain import initialize_multiple_choice_chain
from app.services.config_service import ConfigService

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment setup with defaults
LANGCHAIN_API_KEY = os.getenv('LANGCHAIN_API_KEY')
if LANGCHAIN_API_KEY:
    os.environ['LANGCHAIN_TRACING_V2'] = 'true'
    os.environ['LANGCHAIN_ENDPOINT'] = 'https://api.smith.langchain.com'
    os.environ['LANGCHAIN_API_KEY'] = LANGCHAIN_API_KEY
    logger.info("LangChain tracing enabled")
else:
    logger.warning("LANGCHAIN_API_KEY not found. Tracing will be disabled.")

# Check for GROQ API key
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    GROQ_API_KEY = getpass.getpass("Enter your Groq API key: ")
    os.environ["GROQ_API_KEY"] = GROQ_API_KEY

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./social_assistance.db")

app = FastAPI()

# Create ConfigService instance at module level
config_service = ConfigService(DATABASE_URL)

api_router = APIRouter(prefix="")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:3000", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

file_paths = os.getenv(
    "FILE_PATHS", 
    "data/aides-sociales.json,data/gemeente.json,data/securite-sociale.json"
).split(',')

@app.on_event("startup")
async def startup_event():
    try:
        logger.info("Initializing application...")
        
        # Initialize default configurations
        config_service.initialize_default_configs()
        
        # Get the experiment group from environment variable or use default
        experiment_group = os.getenv("EXPERIMENT_GROUP", "baseline")
        logger.info(f"Using experiment group: {experiment_group}")
        
        # Load documents
        logger.info(f"Loading documents from files: {file_paths}")
        docs = load_documents(file_paths)
        logger.info(f"Loaded {len(docs)} documents")

        # Initialize vectorstore
        logger.info("Initializing vectorstore")
        vectorstore = initialize_vectorstore(docs)
        retriever = vectorstore.as_retriever()

        # Initialize chains with experiment group
        logger.info("Initializing RAG chain")
        retrieval_chain, final_chain, generate_query_back_and_forth = initialize_rag_chain(
            retriever=retriever,
            config_service=config_service,
            experiment_group=experiment_group,
            automatic_verifier=True,
            use_verifier=False
        )

        mc_chain = initialize_multiple_choice_chain(
            config_service=config_service,
            experiment_group=experiment_group
        )

        # Initialize global chain state
        rag_chain.initialize_rag_chain_global(
            retrieval_chain, 
            final_chain, 
            mc_chain, 
            generate_query_back_and_forth,
            config_service
        )
        
        logger.info("Application initialized successfully")
    except Exception as e:
        logger.error(f"Error during initialization: {str(e)}")
        raise

# Include all routers under /api
# api_router.include_router(scraped_data.router)
api_router.include_router(rag_chain.router)
api_router.include_router(speech.router)
api_router.include_router(
    experiments.router,
    prefix="/experiments",
    tags=["experiments"]
)

# Initialize the config service for experiments router
async def get_config_service():
    return config_service

experiments.initialize_router(config_service)

# Include the api_router
app.include_router(api_router)

# Exception handlers
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