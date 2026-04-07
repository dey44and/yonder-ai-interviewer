from __future__ import annotations as _annotations

import asyncio
import sqlite3
import json

from dataclasses import dataclass
from collections.abc import AsyncIterator, Callable
from concurrent.futures.thread import ThreadPoolExecutor
from functools import partial
from typing import Any, TypeVar, List
from typing_extensions import LiteralString, ParamSpec
from contextlib import asynccontextmanager
from pathlib import Path
from models.model import ChatMessage

THIS_DIR = Path(__file__).parent


P = ParamSpec("P")
R = TypeVar("R")


@dataclass
class Database:
    """
    Rudimentary database (implemented as a singleton) to store chat messages in SQLite.

    The SQLite standard library package is synchronous, so we
    use a thread pool executor to run queries asynchronously.
    """

    con: sqlite3.Connection
    _loop: asyncio.AbstractEventLoop
    _executor: ThreadPoolExecutor

    @classmethod
    @asynccontextmanager
    async def connect(
        cls, file: Path = THIS_DIR / ".chat_app_messages.sqlite"
    ) -> AsyncIterator[Database]:
        loop = asyncio.get_event_loop()
        executor = ThreadPoolExecutor(max_workers=1)
        con = await loop.run_in_executor(executor, cls._connect, file)
        slf = cls(con, loop, executor)
        try:
            yield slf
        finally:
            await slf._asyncify(con.close)

    @staticmethod
    def _connect(file: Path) -> sqlite3.Connection:
        con = sqlite3.connect(str(file))
        cur = con.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY, session_id TEXT NOT NULL, message TEXT);"
        )
        con.commit()
        return con

    async def add_message(self, session_id: str, message: str):
        await self._asyncify(
            self._execute,
            "INSERT INTO messages (session_id, message) VALUES (?, ?);",
            session_id,
            message,
            commit=True,
        )

    async def get_messages(self, session_id: str) -> List[ChatMessage]:
        c = await self._asyncify(
            self._execute,
            "SELECT message FROM messages WHERE session_id = ? order by id",
            session_id,
        )
        rows = await self._asyncify(c.fetchall)
        messages: List[ChatMessage] = []
        for row in rows:
            messages.append(json.loads(row[0]))
        return messages

    def _execute(
        self, sql: LiteralString, *args: Any, commit: bool = False
    ) -> sqlite3.Cursor:
        cur = self.con.cursor()
        cur.execute(sql, args)
        if commit:
            self.con.commit()
        return cur

    async def _asyncify(
        self, func: Callable[P, R], *args: P.args, **kwargs: P.kwargs
    ) -> R:
        return await self._loop.run_in_executor(  # type: ignore
            self._executor,
            partial(func, **kwargs),
            *args,  # type: ignore
        )
