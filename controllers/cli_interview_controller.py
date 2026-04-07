import uuid

from models.model import ResponseFormat
from services.agent_service import AgentService
from services.transcript_service import TranscriptService
from datetime import datetime

TOPICS = [
    "AI in the workplace",
    "Productivity tools",
    "Scientific research",
    "AI for education",
]


class CLIInterviewController:
    """Interview controller for CLI app."""

    def __init__(self):
        self.user_id = str(uuid.uuid4())
        self.agent_service: AgentService = AgentService(user_id=self.user_id)
        self.transcript_service: TranscriptService = TranscriptService()

    @staticmethod
    def _format_keywords(keywords: list[str] | None) -> str | None:
        if not keywords:
            return None
        return ", ".join(keywords)

    def _print_agent_response(self, response: ResponseFormat) -> None:
        print(f"\nAgent: {response.response}")
        if response.summary:
            print("\nSummary:")
            print(response.summary)
        formatted_keywords = self._format_keywords(response.keywords)
        if formatted_keywords:
            print("\nKeywords:")
            print(formatted_keywords)
        print("\n")

    def run(self):
        # First, provide an introduction and allow the agent to select a specific topic:
        _init_message = None
        print(
            "🧵 Hello! I am an AI model and I am willing to understand how you are using "
            "AI each day. First of all, please select a topic you are particularly interested in:\n"
            "\t 1. AI in the workplace\n"
            "\t 2. Productivity tools\n"
            "\t 3. Scientific research\n"
            "\t 4. AI for education\n"
        )
        while True:
            try:
                number = int(input("Please type the corresponding number: "))
                if number < 1 or number > 4:
                    raise ValueError(
                        f"Your selected number ({number}) is not a valid choice."
                    )
                _init_message = (
                    f"The user has provided the following interview topic: {TOPICS[number - 1]}. "
                    "You can start the interview."
                )
                break
            except Exception as e:
                print(f"ERROR: {e}")
        current_message = _init_message
        while True:
            # Get the message from the AI
            response = self.agent_service.send_message(current_message)
            self.transcript_service.add_message(
                sender="agent",
                message=response.to_dict(),
                timestamp=datetime.now().isoformat(),
            )
            self._print_agent_response(response)
            # Check if the interview is completed
            if response.interview_complete:
                break
            # Get the message from the user
            current_message = input("You: ")
            self.transcript_service.add_message(
                sender="user",
                message=current_message,
                timestamp=datetime.now().isoformat(),
            )

        # Store the transcript
        filepath = f"results/transcript_{self.user_id}.json"
        self.transcript_service.export_conversation(filepath)
