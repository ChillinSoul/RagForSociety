from langchain_community.embeddings import OllamaEmbeddings
from langchain.embeddings.openai import OpenAIEmbeddings


class LocalEmbeddings:
    def __init__(self):
        # self.embedding_model = OllamaEmbeddings(model="llama3.1")
        self.embedding_model = OpenAIEmbeddings(model="text-embedding-3-large")

    def embed_documents(self, texts):
        return self.embedding_model.embed_documents(texts)
    
    def embed_query(self, text):
        return self.embedding_model.embed_query(text)