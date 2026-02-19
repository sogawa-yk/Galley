"""アプリケーションのテンプレート管理・デプロイを行うサービス。"""

import fnmatch
import json
import shutil
from pathlib import Path

from galley.models.app import AppStatus, DeployResult, TemplateMetadata
from galley.models.errors import (
    AppNotScaffoldedError,
    ArchitectureNotFoundError,
    ProtectedFileError,
    TemplateNotFoundError,
)
from galley.storage.service import StorageService

# ファイルパスで禁止するパターン
_DISALLOWED_PATH_PATTERNS = ("..", "~")


def _validate_file_path(file_path: str) -> str:
    """ファイルパスのトラバーサルを検証する。

    Args:
        file_path: 検証対象のファイルパス。

    Returns:
        検証済みのファイルパス。

    Raises:
        ValueError: パスに不正なパターンが含まれる場合。
    """
    for pattern in _DISALLOWED_PATH_PATTERNS:
        if pattern in file_path:
            raise ValueError(f"Invalid file path: path contains '{pattern}'")
    if file_path.startswith("/"):
        raise ValueError(f"Invalid file path: must be a relative path: {file_path}")
    return file_path


class AppService:
    """アプリケーションのテンプレート管理・デプロイを行う。"""

    def __init__(self, storage: StorageService, config_dir: Path) -> None:
        self._storage = storage
        self._config_dir = config_dir
        self._templates_dir = config_dir / "templates"

    def _app_dir(self, session_id: str) -> Path:
        """セッションのアプリケーションディレクトリを返す。"""
        session_dir = self._storage._session_dir(session_id)
        return session_dir / "app"

    def _snapshots_dir(self, session_id: str) -> Path:
        """セッションのスナップショットディレクトリを返す。"""
        session_dir = self._storage._session_dir(session_id)
        return session_dir / "snapshots"

    def _load_template_metadata(self, template_name: str) -> TemplateMetadata:
        """テンプレートメタデータを読み込む。

        Args:
            template_name: テンプレート名。

        Returns:
            テンプレートメタデータ。

        Raises:
            TemplateNotFoundError: テンプレートが見つからない場合。
        """
        # テンプレート名のサニタイズ
        safe_name = Path(template_name).name
        if safe_name != template_name:
            raise TemplateNotFoundError(template_name)

        template_dir = self._templates_dir / safe_name
        metadata_file = template_dir / "template.json"

        if not metadata_file.exists():
            raise TemplateNotFoundError(template_name)

        data = json.loads(metadata_file.read_text(encoding="utf-8"))
        return TemplateMetadata.model_validate(data)

    async def list_templates(self) -> list[TemplateMetadata]:
        """利用可能なテンプレート一覧を返す。

        Returns:
            テンプレートメタデータのリスト。
        """
        if not self._templates_dir.exists():
            return []

        templates: list[TemplateMetadata] = []
        for template_dir in sorted(self._templates_dir.iterdir()):
            if not template_dir.is_dir():
                continue
            metadata_file = template_dir / "template.json"
            if not metadata_file.exists():
                continue
            try:
                data = json.loads(metadata_file.read_text(encoding="utf-8"))
                templates.append(TemplateMetadata.model_validate(data))
            except (json.JSONDecodeError, ValueError):
                continue
        return templates

    async def scaffold_from_template(
        self,
        session_id: str,
        template_name: str,
        params: dict[str, object],
    ) -> dict[str, object]:
        """テンプレートからプロジェクトを生成する。

        Args:
            session_id: セッションID。
            template_name: テンプレート名。
            params: テンプレートパラメータ。

        Returns:
            生成結果（プロジェクトパスとファイル一覧）。

        Raises:
            SessionNotFoundError: セッションが存在しない場合。
            ArchitectureNotFoundError: アーキテクチャが未設定の場合。
            TemplateNotFoundError: テンプレートが見つからない場合。
        """
        session = await self._storage.load_session(session_id)
        if session.architecture is None:
            raise ArchitectureNotFoundError(session_id)

        metadata = self._load_template_metadata(template_name)

        # テンプレートのappディレクトリを取得
        safe_name = Path(template_name).name
        template_app_dir = self._templates_dir / safe_name / "app"
        if not template_app_dir.exists():
            raise TemplateNotFoundError(template_name)

        # プロジェクトディレクトリにコピー
        app_dir = self._app_dir(session_id)
        if app_dir.exists():
            shutil.rmtree(app_dir)
        shutil.copytree(template_app_dir, app_dir)

        # テンプレートメタデータをセッションディレクトリに保存（protected_paths参照用）
        metadata_save_path = app_dir.parent / "template-metadata.json"
        metadata_save_path.write_text(metadata.model_dump_json(indent=2), encoding="utf-8")

        # パラメータの置換（テンプレートファイル内の {{param_name}} を置換）
        for file_path in app_dir.rglob("*"):
            if not file_path.is_file():
                continue
            try:
                content = file_path.read_text(encoding="utf-8")
                for param_name, param_value in params.items():
                    content = content.replace(f"{{{{{param_name}}}}}", str(param_value))
                file_path.write_text(content, encoding="utf-8")
            except UnicodeDecodeError:
                # バイナリファイルはスキップ
                continue

        # 生成されたファイル一覧
        files = [str(f.relative_to(app_dir)) for f in app_dir.rglob("*") if f.is_file()]

        return {
            "project_path": str(app_dir),
            "template_name": metadata.name,
            "files": sorted(files),
        }

    async def update_app_code(
        self,
        session_id: str,
        file_path: str,
        new_content: str,
    ) -> dict[str, object]:
        """アプリケーションコードを更新する。

        Args:
            session_id: セッションID。
            file_path: 更新対象のファイルパス（app/からの相対パス）。
            new_content: 新しいファイル内容。

        Returns:
            更新結果（スナップショットID含む）。

        Raises:
            SessionNotFoundError: セッションが存在しない場合。
            AppNotScaffoldedError: アプリが未生成の場合。
            ProtectedFileError: 保護ファイルを変更しようとした場合。
            ValueError: パスに不正なパターンが含まれる場合。
        """
        validated_path = _validate_file_path(file_path)

        await self._storage.load_session(session_id)

        app_dir = self._app_dir(session_id)
        if not app_dir.exists():
            raise AppNotScaffoldedError(session_id)

        # テンプレートメタデータからprotected_pathsを取得
        protected_paths = self._get_protected_paths(session_id)
        for pattern in protected_paths:
            if fnmatch.fnmatch(validated_path, pattern):
                raise ProtectedFileError(validated_path)

        # スナップショット保存
        snapshot_id = await self._save_snapshot(session_id)

        # ファイル更新
        target_file = app_dir / validated_path
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_text(new_content, encoding="utf-8")

        return {
            "success": True,
            "snapshot_id": snapshot_id,
            "file_path": validated_path,
        }

    def _get_protected_paths(self, session_id: str) -> list[str]:
        """セッションのアプリに関連するprotected_pathsを取得する。"""
        app_dir = self._app_dir(session_id)
        # テンプレートメタデータがapp内に保存されていればそこから読む
        # 生成時にtemplate.jsonもコピーする設計ではないので、
        # 親ディレクトリからmetadata.jsonを探す
        metadata_file = app_dir.parent / "template-metadata.json"
        if metadata_file.exists():
            try:
                data = json.loads(metadata_file.read_text(encoding="utf-8"))
                metadata = TemplateMetadata.model_validate(data)
                return metadata.protected_paths
            except (json.JSONDecodeError, ValueError):
                pass
        return []

    async def _save_snapshot(self, session_id: str) -> str:
        """アプリディレクトリのスナップショットを保存する。

        Args:
            session_id: セッションID。

        Returns:
            スナップショットID。
        """
        import uuid

        app_dir = self._app_dir(session_id)
        snapshot_id = str(uuid.uuid4())[:8]
        snapshots_dir = self._snapshots_dir(session_id)
        snapshot_dir = snapshots_dir / snapshot_id

        shutil.copytree(app_dir, snapshot_dir)

        return snapshot_id

    async def build_and_deploy(self, session_id: str) -> DeployResult:
        """ビルド・デプロイを実行する。

        現フェーズではOCI DevOps/OKE連携は未実装のため、スタブ応答を返す。

        Args:
            session_id: セッションID。

        Returns:
            デプロイ結果。

        Raises:
            SessionNotFoundError: セッションが存在しない場合。
            AppNotScaffoldedError: アプリが未生成の場合。
        """
        await self._storage.load_session(session_id)

        app_dir = self._app_dir(session_id)
        if not app_dir.exists():
            raise AppNotScaffoldedError(session_id)

        return DeployResult(
            success=False,
            reason="Build and deploy is not yet implemented. "
            "OCI DevOps and OKE integration will be added in a future phase.",
        )

    async def check_app_status(self, session_id: str) -> AppStatus:
        """アプリケーションのデプロイ状態を確認する。

        Args:
            session_id: セッションID。

        Returns:
            アプリケーション状態。

        Raises:
            SessionNotFoundError: セッションが存在しない場合。
        """
        await self._storage.load_session(session_id)

        app_dir = self._app_dir(session_id)
        if not app_dir.exists():
            return AppStatus(session_id=session_id, status="not_deployed")

        return AppStatus(session_id=session_id, status="not_deployed")
