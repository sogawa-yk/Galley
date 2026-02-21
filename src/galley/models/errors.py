"""Galleyのカスタム例外クラス。"""


class GalleyError(Exception):
    """Galleyの基底例外クラス。"""


class SessionNotFoundError(GalleyError):
    """セッションが見つからない場合の例外。"""

    def __init__(self, session_id: str) -> None:
        super().__init__(f"Session not found: {session_id}")
        self.session_id = session_id


class HearingNotCompletedError(GalleyError):
    """ヒアリングが未完了の場合の例外。"""

    def __init__(self, session_id: str) -> None:
        super().__init__(f"Hearing not completed for session: {session_id}")
        self.session_id = session_id


class HearingAlreadyCompletedError(GalleyError):
    """ヒアリングが既に完了している場合の例外。"""

    def __init__(self, session_id: str) -> None:
        super().__init__(f"Hearing already completed for session: {session_id}")
        self.session_id = session_id


class ArchitectureNotFoundError(GalleyError):
    """セッションにアーキテクチャが未設定の場合の例外。"""

    def __init__(self, session_id: str) -> None:
        super().__init__(
            f"Architecture not found for session: {session_id}. "
            "Please call save_architecture first to create an architecture from the hearing results."
        )
        self.session_id = session_id


class ComponentNotFoundError(GalleyError):
    """指定されたコンポーネントが見つからない場合の例外。"""

    def __init__(self, component_id: str) -> None:
        super().__init__(f"Component not found: {component_id}")
        self.component_id = component_id


class StorageError(GalleyError):
    """ストレージ操作のエラー。"""


class TerraformError(GalleyError):
    """Terraform実行エラー。"""

    def __init__(self, message: str, stderr: str, exit_code: int) -> None:
        super().__init__(message)
        self.stderr = stderr
        self.exit_code = exit_code


class OCICliError(GalleyError):
    """OCI CLI実行エラー。"""

    def __init__(self, message: str, command: str, stderr: str, exit_code: int) -> None:
        super().__init__(message)
        self.command = command
        self.stderr = stderr
        self.exit_code = exit_code


class CommandNotAllowedError(GalleyError):
    """ホワイトリスト外のコマンド実行を拒否する例外。"""

    def __init__(self, command: str) -> None:
        super().__init__(f"Command not allowed: {command}")
        self.command = command


class InfraOperationInProgressError(GalleyError):
    """同一セッションで重量操作が実行中の場合の例外。"""

    def __init__(self, session_id: str) -> None:
        super().__init__(f"Infrastructure operation already in progress for session: {session_id}")
        self.session_id = session_id


class TemplateNotFoundError(GalleyError):
    """指定されたテンプレートが見つからない場合の例外。"""

    def __init__(self, template_name: str) -> None:
        super().__init__(f"Template not found: {template_name}")
        self.template_name = template_name


class ProtectedFileError(GalleyError):
    """保護されたファイルの変更を拒否する例外。"""

    def __init__(self, file_path: str) -> None:
        super().__init__(f"Protected file cannot be modified: {file_path}")
        self.file_path = file_path


class AppNotScaffoldedError(GalleyError):
    """アプリケーションが未生成の場合の例外。"""

    def __init__(self, session_id: str) -> None:
        super().__init__(f"Application not scaffolded for session: {session_id}")
        self.session_id = session_id
