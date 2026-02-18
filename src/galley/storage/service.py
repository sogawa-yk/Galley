"""ローカルファイルシステムベースのストレージサービス。"""

import json
import shutil
from pathlib import Path

from galley.models.errors import SessionNotFoundError, StorageError
from galley.models.session import Session


class StorageService:
    """ローカルファイルシステムを利用したデータ永続化層。

    MVP段階ではローカルファイルシステムに保存する。
    将来的にOCI Object Storage実装に切り替え可能な設計。
    """

    def __init__(self, data_dir: Path) -> None:
        self._data_dir = data_dir
        self._sessions_dir = data_dir / "sessions"

    def _session_dir(self, session_id: str) -> Path:
        # ディレクトリトラバーサル防止
        safe_id = Path(session_id).name
        if safe_id != session_id:
            raise StorageError(f"Invalid session ID: {session_id}")
        return self._sessions_dir / safe_id

    def _session_file(self, session_id: str) -> Path:
        return self._session_dir(session_id) / "session.json"

    async def save_session(self, session: Session) -> None:
        """セッションをファイルシステムに保存する。"""
        session_dir = self._session_dir(session.id)
        session_dir.mkdir(parents=True, exist_ok=True)
        session_file = self._session_file(session.id)
        session_file.write_text(session.model_dump_json(indent=2), encoding="utf-8")

    async def load_session(self, session_id: str) -> Session:
        """セッションをファイルシステムから読み込む。

        Raises:
            SessionNotFoundError: セッションが存在しない場合。
        """
        session_file = self._session_file(session_id)
        if not session_file.exists():
            raise SessionNotFoundError(session_id)
        data = json.loads(session_file.read_text(encoding="utf-8"))
        return Session.model_validate(data)

    async def delete_session(self, session_id: str) -> None:
        """セッションをファイルシステムから削除する。"""
        session_dir = self._session_dir(session_id)
        if session_dir.exists():
            shutil.rmtree(session_dir)

    async def list_sessions(self) -> list[str]:
        """保存されているセッションIDの一覧を返す。"""
        if not self._sessions_dir.exists():
            return []
        return [d.name for d in self._sessions_dir.iterdir() if d.is_dir()]
