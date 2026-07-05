from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    emotion: str
    crisis: bool
    resources: Optional[List[Dict[str, Any]]] = None