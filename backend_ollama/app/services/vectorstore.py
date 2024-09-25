import os
import json
from typing import List
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from .embedding import LocalEmbeddings
import logging

logger = logging.getLogger(__name__)

def initialize_vectorstore(docs: List[Document], persist_directory: str = "./chroma", batch_size: int = 100):
    logger.info(f"Starting vectorstore initialization with {len(docs)} documents")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(docs)
    logger.info(f"Split documents into {len(splits)} chunks")

    local_embeddings = LocalEmbeddings()

    # Check if we have a checkpoint file
    checkpoint_file = os.path.join(persist_directory, "embedding_checkpoint.json")
    start_index = 0
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, 'r') as f:
            checkpoint_data = json.load(f)
            start_index = checkpoint_data.get('last_processed_index', 0)
        logger.info(f"Resuming from checkpoint: {start_index}/{len(splits)} chunks processed")

    if os.path.exists(persist_directory) and len(os.listdir(persist_directory)) > 0 and start_index > 0:
        logger.info("Loading existing vectorstore")
        vectorstore = Chroma(persist_directory=persist_directory, embedding_function=local_embeddings)
    else:
        logger.info("Creating new vectorstore")
        vectorstore = Chroma(persist_directory=persist_directory, embedding_function=local_embeddings)

    total_splits = len(splits)
    for i in range(start_index, total_splits, batch_size):
        end_index = min(i + batch_size, total_splits)
        batch = splits[i:end_index]
        try:
            logger.info(f"Processing batch {i}-{end_index} of {total_splits}")
            vectorstore.add_documents(documents=batch)
            # Update checkpoint
            with open(checkpoint_file, 'w') as f:
                json.dump({'last_processed_index': end_index}, f)
            logger.info(f"Processed {end_index}/{total_splits} chunks ({(end_index/total_splits)*100:.2f}%)")
        except Exception as e:
            logger.error(f"Error processing batch {i}-{end_index}: {str(e)}")
            # The checkpoint will allow us to resume from the last successful batch
            break

    vectorstore.persist()
    logger.info("Vectorstore initialization completed")
    return vectorstore