from langchain_community.embeddings import OllamaEmbeddings

class LocalEmbeddings:
    def __init__(self):
        self.embedding_model = OllamaEmbeddings(model="llama3.1")

    def embed_documents(self, texts):
        return self.embedding_model.embed_documents(texts)
    
    def embed_query(self, text):
        return self.embedding_model.embed_query(text)