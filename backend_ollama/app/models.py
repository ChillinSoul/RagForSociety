from pydantic import BaseModel
from typing import List, Optional, Dict

class ScrapedData(BaseModel):
    url: str
    breadcrumbs: dict
    main_heading: Optional[str] = None
    content: List[str]
    image: dict
    table_rows: Optional[List[str]] = []
    conditions: Optional[List[str]] = []

class QuestionRequest(BaseModel):
    question: str

class Questionaire():
    question: str
    reponse: str

class QuestionBackAndForthRequest(BaseModel):
    question: str
    questionaire: List[dict[str, str]]

class TokenCount(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class ApiResponse(BaseModel):
    retriever_results: list
    llm_response: str
    mc_response: dict
    token_counts: TokenCount