import asyncio
import json

import pytest

import chat_app
from models.model import ChatMessage


class FakeDatabase:
    def __init__(self):
        self.messages: dict[str, list[ChatMessage]] = {}

    async def add_message(self, session_id: str, message: str) -> None:
        self.messages.setdefault(session_id, []).append(json.loads(message))

    async def get_messages(self, session_id: str) -> list[ChatMessage]:
        return list(self.messages.get(session_id, []))


class FakeWebInterviewController:
    def __init__(self):
        self.user_id = "session-123"
        self.calls: list[str] = []

    def run(self, message: str) -> ChatMessage:
        self.calls.append(message)
        if len(self.calls) == 1:
            return {
                "role": "model",
                "timestamp": "2026-04-07T10:00:00+00:00",
                "message": "What kind of work do you do?",
                "interview_completed": False,
            }
        return {
            "role": "model",
            "timestamp": "2026-04-07T10:01:00+00:00",
            "message": "Thanks for sharing.\n\nSummary:\nAI helps with writing.\n\nKeywords:\nAI, writing",
            "interview_completed": True,
        }


async def collect_streaming_body(response) -> bytes:
    body = b""
    async for chunk in response.body_iterator:
        body += chunk
    return body


@pytest.fixture(autouse=True)
def clear_sessions():
    chat_app.sessions.clear()
    yield
    chat_app.sessions.clear()


def test_start_interview_returns_session_id_and_persists_first_message(monkeypatch):
    fake_database = FakeDatabase()
    monkeypatch.setattr(chat_app, "WebInterviewController", FakeWebInterviewController)

    result = asyncio.run(
        chat_app.start_interview(
            chat_app.StartInterviewRequest(topic="AI in the workplace"),
            database=fake_database,
        )
    )

    assert result["session_id"] == "session-123"
    assert result["message"]["message"] == "What kind of work do you do?"
    assert fake_database.messages["session-123"] == [result["message"]]


def test_post_chat_streams_user_and_model_messages_and_persists_them():
    fake_database = FakeDatabase()
    controller = FakeWebInterviewController()
    controller.run("AI in the workplace")
    chat_app.sessions["session-123"] = controller

    response = asyncio.run(
        chat_app.post_chat(
            "session-123",
            prompt="I work in marketing.",
            database=fake_database,
        )
    )
    body = asyncio.run(collect_streaming_body(response))
    streamed_messages = [
        json.loads(line) for line in body.decode("utf-8").splitlines() if line
    ]

    assert streamed_messages[0]["role"] == "user"
    assert streamed_messages[0]["message"] == "I work in marketing."
    assert streamed_messages[0]["interview_completed"] is False
    assert streamed_messages[1]["role"] == "model"
    assert streamed_messages[1]["interview_completed"] is True
    assert fake_database.messages["session-123"] == streamed_messages


def test_get_chat_returns_newline_delimited_json():
    fake_database = FakeDatabase()
    fake_database.messages["session-123"] = [
        {
            "role": "model",
            "timestamp": "2026-04-07T10:00:00+00:00",
            "message": "What kind of work do you do?",
            "interview_completed": False,
        }
    ]

    response = asyncio.run(chat_app.get_chat("session-123", database=fake_database))
    payload = response.body.decode("utf-8").splitlines()

    assert [json.loads(line) for line in payload] == fake_database.messages[
        "session-123"
    ]
