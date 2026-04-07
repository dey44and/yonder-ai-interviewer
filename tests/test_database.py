import asyncio
import json

from persistence.database import Database


def test_database_stores_messages_by_session(tmp_path):
    async def scenario():
        db_path = tmp_path / "messages.sqlite"
        async with Database.connect(db_path) as database:
            await database.add_message(
                "session-one",
                json.dumps(
                    {
                        "role": "model",
                        "timestamp": "2026-04-07T10:00:00",
                        "message": "First question",
                        "interview_completed": False,
                    }
                ),
            )
            await database.add_message(
                "session-two",
                json.dumps(
                    {
                        "role": "user",
                        "timestamp": "2026-04-07T10:01:00",
                        "message": "Other session",
                        "interview_completed": False,
                    }
                ),
            )
            await database.add_message(
                "session-one",
                json.dumps(
                    {
                        "role": "user",
                        "timestamp": "2026-04-07T10:02:00",
                        "message": "Answer",
                        "interview_completed": False,
                    }
                ),
            )

            return (
                await database.get_messages("session-one"),
                await database.get_messages("session-two"),
            )

    session_one_messages, session_two_messages = asyncio.run(scenario())

    assert [message["message"] for message in session_one_messages] == [
        "First question",
        "Answer",
    ]
    assert [message["role"] for message in session_one_messages] == [
        "model",
        "user",
    ]
    assert [message["message"] for message in session_two_messages] == ["Other session"]


def test_database_returns_empty_list_for_unknown_session(tmp_path):
    async def scenario():
        db_path = tmp_path / "messages.sqlite"
        async with Database.connect(db_path) as database:
            return await database.get_messages("missing-session")

    assert asyncio.run(scenario()) == []
