from enum import Enum
from datetime import datetime
from typing import Dict
import uuid

from models.model import ResponseFormat
from services.agent_service import AgentService
from services.textanalysis_service import TextAnalysisService
from services.transcript_service import TranscriptService


class States(Enum):
    NOT_STARTED = 1
    ACTIVE = 2
    COMPLETED = 3


class WebInterviewController:
    """Interview controller for web app."""

    def __init__(self):
        self._user_id = str(uuid.uuid4())
        self.agent_service: AgentService = AgentService(user_id=self._user_id)
        self.transcript_service: TranscriptService = TranscriptService()

        self.states = {
            States.NOT_STARTED: self.run_not_started,
            States.ACTIVE: self.run_active,
            States.COMPLETED: self.run_completed,
        }
        self.state: States = States.NOT_STARTED

    @property
    def user_id(self) -> str:
        return self._user_id

    @staticmethod
    def _format_final_message(response: ResponseFormat) -> str:
        sections = [response.response]
        if response.summary:
            sections.append(f"Summary:\n{response.summary}")
        if response.keywords:
            sections.append(f"Keywords:\n{', '.join(response.keywords)}")
        return "\n\n".join(sections)

    def run_not_started(self, message: str) -> Dict[str, str]:
        """
        Initializes the agent by providing the selected topic.

        Args:
            message (str): The chosen topic by user.

        Returns:
            A dictionary with the following format:
            {
                "role" = ...,
                "message" = ...,
                "timestamp" = ...
            }
        """
        current_message = (
            f"The user has provided the following interview topic: {message}. "
            "You can start the interview."
        )
        # Get the message from the AI
        response = self.agent_service.send_message(current_message)
        self.transcript_service.add_message(
            sender="agent",
            message=response.to_dict(),
            timestamp=datetime.now().isoformat(),
        )
        self.state = States.ACTIVE
        return {
            "role": "model",
            "message": response.response,
            "timestamp": datetime.now().isoformat(),
            "interview_completed": False,
        }

    def run_active(self, message: str) -> Dict[str, str]:
        """
        Provides the model with the answer supplied by user.

        Args:
            message (str): The message from user.

        Returns:
            A dictionary with the following format:
            {
                "role" = ...,
                "message" = ...,
                "timestamp" = ...
            }
        """
        # Get the message from the AI
        response = self.agent_service.send_message(message)
        self.transcript_service.add_message(
            sender="agent",
            message=response.to_dict(),
            timestamp=datetime.now().isoformat(),
        )
        self.state = States.COMPLETED if response.interview_complete else States.ACTIVE

        if self.state == States.COMPLETED:
            # Store the transcript
            filepath = f"results/transcript_{self.user_id}.json"
            self.transcript_service.export_conversation(filepath)
        message = (
            response.response
            if self.state == States.ACTIVE
            else self._format_final_message(response)
        )

        return {
            "role": "model",
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "interview_completed": self.state == States.COMPLETED,
        }

    def run_completed(self, message: str) -> Dict[str, str]:
        """
        Sends back the same message and notice the caller that the discussion is ended.

        Args:
            message (str): The message from user.

        Returns:
            A dictionary with the following format:
            {
                "role" = ...,
                "message" = ...,
                "timestamp" = ...
            }
        """
        return {
            "role": "model",
            "message": "The interview has already been completed.",
            "timestamp": datetime.now().isoformat(),
            "interview_completed": True,
        }

    def run(self, message: str):
        """
        Calls the corresponding method and advances to the next state.

        Args:
            message (str): The message from user.

        Returns:
            A dictionary with the following format:
            {
                "role" = ...,
                "message" = ...,
                "timestamp" = ...
            }
        """
        return self.states[self.state](message)
