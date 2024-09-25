import json
from pathlib import Path
from typing import List
from langchain_core.documents import Document

def load_documents(file_path: str) -> List[Document]:
    file = Path(file_path)
    with file.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return [Document(page_content=" ".join(doc["content"]), metadata={"url": doc["url"]}) for doc in data]