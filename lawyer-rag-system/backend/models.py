from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class DocumentInfo(BaseModel):
    document_id: str
    filename: str
    category: str
    upload_time: datetime
    status: str  # "processing", "completed", "failed"

class QueryRequest(BaseModel):
    query: str
    filters: Optional[Dict[str, Any]] = None

class QueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]


class UploadResponse(BaseModel):
    filename: str
    document_id: str
    message: str
    status: str