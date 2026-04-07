from models.model import ResponseFormat
import controllers.web_interview_controller as web_controller


class FakeAgentService:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.messages: list[str] = []
        self._responses = [
            ResponseFormat(
                response="What is your role?",
                question_type="new_question",
                question_number=1,
                interview_complete=False,
            ),
            ResponseFormat(
                response="Thanks for sharing.",
                question_type="closing",
                question_number=3,
                interview_complete=True,
                keywords=["AI", "workplace", "copywriting"],
                summary="The interviewee uses AI regularly in their work.",
            ),
        ]

    def send_message(self, message: str) -> ResponseFormat:
        self.messages.append(message)
        return self._responses[len(self.messages) - 1]


def test_web_controller_advances_state_and_formats_final_message(monkeypatch):
    monkeypatch.setattr(web_controller, "AgentService", FakeAgentService)

    controller = web_controller.WebInterviewController()
    exported: dict[str, str] = {}
    controller.transcript_service.export_conversation = lambda path: exported.update(
        {"path": path}
    )

    first_message = controller.run("AI in the workplace")

    assert first_message["role"] == "model"
    assert first_message["message"] == "What is your role?"
    assert first_message["interview_completed"] is False
    assert controller.state == web_controller.States.ACTIVE
    assert controller.agent_service.messages[0].startswith(
        "The user has provided the following interview topic: AI in the workplace."
    )

    final_message = controller.run("I work in marketing.")

    assert final_message["interview_completed"] is True
    assert "Thanks for sharing." in final_message["message"]
    assert (
        "Summary:\nThe interviewee uses AI regularly in their work."
        in final_message["message"]
    )
    assert "Keywords:\nAI, workplace, copywriting" in final_message["message"]
    assert controller.state == web_controller.States.COMPLETED
    assert exported["path"].endswith(f"results/transcript_{controller.user_id}.json")


def test_web_controller_rejects_messages_after_completion(monkeypatch):
    monkeypatch.setattr(web_controller, "AgentService", FakeAgentService)

    controller = web_controller.WebInterviewController()
    controller.transcript_service.export_conversation = lambda path: None
    controller.run("AI in the workplace")
    controller.run("I work in marketing.")

    response = controller.run("Another answer")

    assert response["role"] == "model"
    assert response["message"] == "The interview has already been completed."
    assert response["interview_completed"] is True
