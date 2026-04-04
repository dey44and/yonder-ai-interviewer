from dataclasses import dataclass
from dataclasses_json import dataclass_json
from typing import Literal, Optional


@dataclass
class Context:
    """Custom runtime context schema."""

    user_id: str


@dataclass_json
@dataclass
class ResponseFormat:
    """Response schema for the agent."""

    response: str
    question_type: Literal["new_question", "follow_up", "closing"]
    question_number: int
    interview_complete: bool
    summary: Optional[str] = None
