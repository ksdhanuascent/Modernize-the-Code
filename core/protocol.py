from pydantic import BaseModel, Field
from typing import Optional, Any, Dict, List

class AgentMessage(BaseModel):
    """Standard message envelope passed between agents."""
    sender: str = Field(..., description="Name of the sending agent")
    recipient: str = Field(..., description="Name of the receiving agent")
    task_type: str = Field(..., description="Type of task (e.g., 'analyze', 'refactor', 'test')")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Data payload (code, context, etc.)")
    timestamp: Optional[str] = None

class TaskResult(BaseModel):
    """Structured result returned by an agent."""
    success: bool = Field(..., description="Whether the agent completed the task successfully")
    data: Optional[Dict[str, Any]] = Field(None, description="The output data (e.g., refactored code)")
    error_message: Optional[str] = Field(None, description="Detailed error if success is False")
    syntax_errors: List[str] = Field(default_factory=list, description="List of specific syntax errors found")
    sender: str = Field(..., description="Name of the agent who produced this result")
    language: Optional[str] = Field(default=None, description="Target programming language of the code/task")

    def to_json_string(self) -> str:
        return self.model_dump_json(indent=2)
