import uuid

from models.model import ResponseFormat
from services.agent_service import AgentService
from services.textanalysis_service import TextAnalysisService
from services.transcript_service import TranscriptService
from datetime import datetime


class InterviewController:
    def __init__(self, topic: str = "AI in the workplace"):
        self._init_message = (
            f"The user has provided the following interview topic: {topic}. "
            "You can start the interview."
        )

        self.user_id = str(uuid.uuid4())
        self.agent_service: AgentService = AgentService(user_id=self.user_id)
        self.transcript_service: TranscriptService = TranscriptService()
        self.textanalysis_service: TextAnalysisService = TextAnalysisService()

    def _print_agent_response(self, response: ResponseFormat) -> None:
        print(f"\nAgent: {response.response}")
        if response.summary:
            print("\nSummary:")
            print(response.summary)
        print("\n")

    def run(self):
        current_message = self._init_message
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

        # Generate the analysis
        print(
            self.textanalysis_service.analyze_transcript(
                self.transcript_service.transcript
            )
        )
