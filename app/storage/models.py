from pydantic import BaseModel
from typing import Optional, Dict, Any

class RunEntry(BaseModel):
    id: str
    status: str
    result: Optional[Dict[str, Any]]
