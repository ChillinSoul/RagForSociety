import json
from pathlib import Path
from typing import List
from langchain_core.documents import Document

def load_documents(file_paths: List[str]) -> List[Document]:
    all_documents = []
    for file_path in file_paths:
        file = Path(file_path)
        if file.is_file():
            with file.open("r", encoding="utf-8") as f:
                data = json.load(f)
                documents = [
                    Document(
                        page_content=doc.get("content") or doc.get("converted_markdown") or doc.get("summary"),
                        metadata={"url": doc["url"]}
                    )
                    for doc in data.values()
                ]
                all_documents.extend(documents)
        else:
            print(f"Warning: {file_path} does not exist or is not a file.")
    return all_documents
