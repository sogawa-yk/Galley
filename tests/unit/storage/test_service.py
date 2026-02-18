"""StorageServiceのユニットテスト。"""

import pytest

from galley.models.errors import SessionNotFoundError, StorageError
from galley.models.session import Answer, Session
from galley.storage.service import StorageService


class TestStorageService:
    async def test_save_and_load_session(self, storage: StorageService) -> None:
        session = Session(id="test-session-1")
        await storage.save_session(session)

        loaded = await storage.load_session("test-session-1")
        assert loaded.id == "test-session-1"
        assert loaded.status == "in_progress"

    async def test_load_nonexistent_session_raises_error(self, storage: StorageService) -> None:
        with pytest.raises(SessionNotFoundError) as exc_info:
            await storage.load_session("nonexistent")
        assert exc_info.value.session_id == "nonexistent"

    async def test_save_session_with_answers(self, storage: StorageService) -> None:
        session = Session(id="test-session-2")
        session.answers["q1"] = Answer(question_id="q1", value="answer1")
        await storage.save_session(session)

        loaded = await storage.load_session("test-session-2")
        assert "q1" in loaded.answers
        assert loaded.answers["q1"].value == "answer1"

    async def test_save_session_overwrites_existing(self, storage: StorageService) -> None:
        session = Session(id="test-session-3")
        await storage.save_session(session)

        session.status = "completed"
        await storage.save_session(session)

        loaded = await storage.load_session("test-session-3")
        assert loaded.status == "completed"

    async def test_delete_session(self, storage: StorageService) -> None:
        session = Session(id="test-session-4")
        await storage.save_session(session)
        await storage.delete_session("test-session-4")

        with pytest.raises(SessionNotFoundError):
            await storage.load_session("test-session-4")

    async def test_delete_nonexistent_session_no_error(self, storage: StorageService) -> None:
        await storage.delete_session("nonexistent")

    async def test_list_sessions_empty(self, storage: StorageService) -> None:
        sessions = await storage.list_sessions()
        assert sessions == []

    async def test_list_sessions(self, storage: StorageService) -> None:
        await storage.save_session(Session(id="session-a"))
        await storage.save_session(Session(id="session-b"))

        sessions = await storage.list_sessions()
        assert sorted(sessions) == ["session-a", "session-b"]

    async def test_directory_traversal_prevention(self, storage: StorageService) -> None:
        with pytest.raises(StorageError):
            await storage.load_session("../../../etc/passwd")
