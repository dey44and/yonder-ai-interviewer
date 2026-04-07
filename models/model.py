from dataclasses import dataclass
from dataclasses_json import dataclass_json
from typing import Literal, Optional, List
from typing_extensions import TypedDict


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
    keywords: Optional[List[str]] = None
    summary: Optional[str] = None


class ChatMessage(TypedDict):
    """Format of messages sent to the browser."""

    role: Literal["user", "model"]
    timestamp: str
    message: str
    interview_completed: bool
