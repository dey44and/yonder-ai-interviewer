"""
Simple chat app example build with FastAPI.

Reference implementation: https://ai.pydantic.dev/examples/chat-app/#example-code
"""

from __future__ import annotations as _annotations

import json
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Dict, List

import fastapi
from fastapi import Depends, Request
from fastapi.responses import FileResponse, Response, StreamingResponse
from pydantic import BaseModel

from controllers.web_interview_controller import WebInterviewController
from persistence.database import Database
from models.model import ChatMessage

THIS_DIR = Path(__file__).parent


@asynccontextmanager
async def lifespan(_app: fastapi.FastAPI):
    async with Database.connect() as db:
        yield {"db": db}


async def get_db(request: Request) -> Database:
    return request.state.db


sessions: Dict[str, WebInterviewController] = {}
app = fastapi.FastAPI(lifespan=lifespan)

################################################
# Get Methods for index.html and for chat_app.ts
################################################


@app.get("/")
async def index() -> FileResponse:
    return FileResponse((THIS_DIR / "templates/chat_app.html"), media_type="text/html")


@app.get("/chat_app.ts")
async def main_ts() -> FileResponse:
    """Get the raw typescript code, it's compiled in the browser, forgive me."""
    return FileResponse((THIS_DIR / "static/chat_app.ts"), media_type="text/plain")


##############################################
# Methods for interview management (GET, POST)
##############################################


class StartInterviewRequest(BaseModel):
    """Format of start interview request message."""

    topic: str


@app.get("/interview/{session_id}")
async def get_chat(session_id: str, database: Database = Depends(get_db)) -> Response:
    msgs: List[ChatMessage] = await database.get_messages(session_id)
    return Response(
        b"\n".join(json.dumps(m).encode("utf-8") for m in msgs),
        media_type="text/plain",
    )


@app.post("/interview/start")
async def start_interview(
    payload: StartInterviewRequest, database: Database = Depends(get_db)
):
    """Initiates the interview and returns the session id, and the first question."""
    # Creates a new controller and stores it
    controller = WebInterviewController()
    session_id = controller.user_id
    sessions[session_id] = controller

    # Get the initial message
    init_message = controller.run(payload.topic)
    await database.add_message(session_id, json.dumps(init_message))

    return {"session_id": session_id, "message": init_message}


@app.post("/interview/{session_id}/message")
async def post_chat(
    session_id: str,
    prompt: Annotated[str, fastapi.Form()],
    database: Database = Depends(get_db),
) -> StreamingResponse:
    async def stream_messages():
        """Streams new line delimited JSON `Message`s to the client."""
        # stream the user prompt so that can be displayed straight away
        question: ChatMessage = {
            "role": "user",
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "message": prompt,
            "interview_completed": False,
        }
        yield json.dumps(question).encode("utf-8") + b"\n"
        await database.add_message(session_id, json.dumps(question))

        # run the agent with the user prompt
        result: ChatMessage = sessions[session_id].run(prompt)
        yield json.dumps(result).encode("utf-8") + b"\n"
        await database.add_message(session_id, json.dumps(result))

    return StreamingResponse(stream_messages(), media_type="text/plain")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("chat_app:app", reload=True, reload_dirs=[str(THIS_DIR)])
