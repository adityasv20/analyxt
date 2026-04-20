"""
schemas.py — All Pydantic models for request/response validation.
"""

from pydantic import BaseModel
from typing import Any, Dict, List, Optional


class DatasetOverview(BaseModel):
    rows: int
    columns: int
    column_names: List[str]
    dtypes: Dict[str, str]
    missing_values: Dict[str, int]
    duplicate_rows: int
    numeric_columns: List[str]
    categorical_columns: List[str]
    memory_usage_kb: float


class FindingItem(BaseModel):
    label: str
    value: Any
    note: Optional[str] = None


class AnalysisRequest(BaseModel):
    filename: str
    prompt: str


class AnalysisResult(BaseModel):
    dataset_overview: Optional[DatasetOverview] = None
    plan: List[str] = []
    findings: List[FindingItem] = []
    chart_paths: List[str] = []
    llm_summary: str = ""
    report_text: str = ""
    report_filename: Optional[str] = None
    error: Optional[str] = None


class ChatMessage(BaseModel):
    role: str       # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    filename: str
    question: str
    history: List[ChatMessage] = []


class ChatResponse(BaseModel):
    answer: str
    method: str     # "pandas" | "gemini"
    question: str


class EmailRequest(BaseModel):
    to_email: str
    report_filename: str
    subject: Optional[str] = "Your Analyzt Report"
