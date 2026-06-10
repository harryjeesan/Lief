from pydantic import BaseModel
from typing import Optional

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    conversation_id: Optional[str] = None

class ExecuteRequest(BaseModel):
    command: str

class BrowseRequest(BaseModel):
    script: str

class AgentRequest(BaseModel):
    task: str

class AgentApproveRequest(BaseModel):
    approval_id: str
    approved: bool

class GenerateRequest(BaseModel):
    system_prompt: str
    user_prompt: str
    is_json_mode: bool = False

class DistillRequest(BaseModel):
    task: str
    history: list
