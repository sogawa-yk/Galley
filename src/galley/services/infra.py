"""インフラストラクチャの構築・管理を行うサービス。"""

import asyncio
import re
import shlex
from pathlib import Path

from galley.models.errors import (
    ArchitectureNotFoundError,
    CommandNotAllowedError,
    InfraOperationInProgressError,
)
from galley.models.infra import CLIResult, TerraformResult
from galley.storage.service import StorageService

# terraform_dirで禁止するパスパターン
_DISALLOWED_PATH_PATTERNS = ("..", "~")


def _validate_terraform_dir(terraform_dir: str) -> Path:
    """terraform_dirのパストラバーサルを検証する。

    Args:
        terraform_dir: Terraformファイルが格納されたディレクトリパス。

    Returns:
        解決済みの絶対パス。

    Raises:
        ValueError: パスに不正なパターンが含まれる場合。
    """
    for pattern in _DISALLOWED_PATH_PATTERNS:
        if pattern in terraform_dir:
            raise ValueError(f"Invalid terraform_dir: path contains '{pattern}'")
    resolved = Path(terraform_dir).resolve()
    if not resolved.is_absolute():
        raise ValueError(f"Invalid terraform_dir: must be an absolute path: {terraform_dir}")
    return resolved


# OCI CLIで許可されるサービスコマンドのホワイトリスト
ALLOWED_OCI_SERVICES: frozenset[str] = frozenset(
    {
        "iam",
        "compute",
        "network",
        "bv",
        "os",
        "db",
        "container-instances",
        "resource-manager",
        "dns",
        "oke",
        "apigateway",
        "functions",
        "events",
        "logging",
        "monitoring",
        "vault",
        "kms",
        "artifacts",
        "devops",
    }
)

# Terraform plan出力からサマリーを抽出する正規表現
_PLAN_SUMMARY_RE = re.compile(r"(\d+ to add, \d+ to change, \d+ to destroy)")


class InfraService:
    """インフラストラクチャの構築・管理を行う。"""

    def __init__(self, storage: StorageService, config_dir: Path) -> None:
        self._storage = storage
        self._config_dir = config_dir
        # セッション単位の排他ロック
        self._session_locks: dict[str, asyncio.Lock] = {}

    def _get_session_lock(self, session_id: str) -> asyncio.Lock:
        """セッション単位のasyncio.Lockを取得する。"""
        if session_id not in self._session_locks:
            self._session_locks[session_id] = asyncio.Lock()
        return self._session_locks[session_id]

    async def _run_subprocess(self, args: list[str], cwd: str | None = None) -> tuple[int, str, str]:
        """サブプロセスを非同期で実行し、結果を返す。

        Args:
            args: 実行するコマンドと引数のリスト。
            cwd: 作業ディレクトリ。

        Returns:
            (exit_code, stdout, stderr) のタプル。
        """
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
        )
        stdout_bytes, stderr_bytes = await proc.communicate()
        return (
            proc.returncode or 0,
            stdout_bytes.decode("utf-8", errors="replace"),
            stderr_bytes.decode("utf-8", errors="replace"),
        )

    def _extract_plan_summary(self, stdout: str) -> str | None:
        """Terraform plan出力からサマリー行を抽出する。"""
        match = _PLAN_SUMMARY_RE.search(stdout)
        if match:
            return match.group(1)
        # "No changes" のケースも検出
        if "No changes" in stdout or "no changes" in stdout.lower():
            return "No changes. Infrastructure is up-to-date."
        return None

    async def run_terraform_plan(self, session_id: str, terraform_dir: str) -> TerraformResult:
        """Terraform planを実行する。

        Args:
            session_id: セッションID。
            terraform_dir: Terraformファイルが格納されたディレクトリパス。

        Returns:
            Terraform実行結果。

        Raises:
            SessionNotFoundError: セッションが存在しない場合。
            ArchitectureNotFoundError: アーキテクチャが未設定の場合。
            InfraOperationInProgressError: 同一セッションで操作が実行中の場合。
        """
        validated_dir = _validate_terraform_dir(terraform_dir)

        session = await self._storage.load_session(session_id)
        if session.architecture is None:
            raise ArchitectureNotFoundError(session_id)

        lock = self._get_session_lock(session_id)
        if lock.locked():
            raise InfraOperationInProgressError(session_id)

        async with lock:
            exit_code, stdout, stderr = await self._run_subprocess(
                ["terraform", "plan", "-no-color", "-input=false"],
                cwd=str(validated_dir),
            )

        plan_summary = self._extract_plan_summary(stdout) if exit_code == 0 else None

        return TerraformResult(
            success=exit_code == 0,
            command="plan",
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
            plan_summary=plan_summary,
        )

    async def run_terraform_apply(self, session_id: str, terraform_dir: str) -> TerraformResult:
        """Terraform applyを実行する。

        Args:
            session_id: セッションID。
            terraform_dir: Terraformファイルが格納されたディレクトリパス。

        Returns:
            Terraform実行結果。

        Raises:
            SessionNotFoundError: セッションが存在しない場合。
            ArchitectureNotFoundError: アーキテクチャが未設定の場合。
            InfraOperationInProgressError: 同一セッションで操作が実行中の場合。
        """
        validated_dir = _validate_terraform_dir(terraform_dir)

        session = await self._storage.load_session(session_id)
        if session.architecture is None:
            raise ArchitectureNotFoundError(session_id)

        lock = self._get_session_lock(session_id)
        if lock.locked():
            raise InfraOperationInProgressError(session_id)

        async with lock:
            exit_code, stdout, stderr = await self._run_subprocess(
                ["terraform", "apply", "-auto-approve", "-no-color", "-input=false"],
                cwd=str(validated_dir),
            )

        return TerraformResult(
            success=exit_code == 0,
            command="apply",
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
        )

    async def run_terraform_destroy(self, session_id: str, terraform_dir: str) -> TerraformResult:
        """Terraform destroyを実行する。

        Args:
            session_id: セッションID。
            terraform_dir: Terraformファイルが格納されたディレクトリパス。

        Returns:
            Terraform実行結果。

        Raises:
            SessionNotFoundError: セッションが存在しない場合。
            ArchitectureNotFoundError: アーキテクチャが未設定の場合。
            InfraOperationInProgressError: 同一セッションで操作が実行中の場合。
        """
        validated_dir = _validate_terraform_dir(terraform_dir)

        session = await self._storage.load_session(session_id)
        if session.architecture is None:
            raise ArchitectureNotFoundError(session_id)

        lock = self._get_session_lock(session_id)
        if lock.locked():
            raise InfraOperationInProgressError(session_id)

        async with lock:
            exit_code, stdout, stderr = await self._run_subprocess(
                ["terraform", "destroy", "-auto-approve", "-no-color", "-input=false"],
                cwd=str(validated_dir),
            )

        return TerraformResult(
            success=exit_code == 0,
            command="destroy",
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
        )

    def _validate_oci_command(self, command: str) -> list[str]:
        """OCI CLIコマンドをホワイトリストで検証し、引数リストを返す。

        Args:
            command: OCI CLIコマンド文字列（例: "oci compute instance list --compartment-id ..."）。

        Returns:
            検証済みの引数リスト。

        Raises:
            CommandNotAllowedError: コマンドがホワイトリスト外の場合。
        """
        try:
            args = shlex.split(command)
        except ValueError as e:
            raise CommandNotAllowedError(command) from e

        if not args:
            raise CommandNotAllowedError(command)

        # "oci" プレフィックスの処理
        if args[0] == "oci":
            args = args[1:]

        if not args:
            raise CommandNotAllowedError(command)

        # 最初の引数がホワイトリスト内のサービスか検証
        service = args[0]
        if service not in ALLOWED_OCI_SERVICES:
            raise CommandNotAllowedError(command)

        # 完全な引数リストを返す（"oci" を先頭に付与）
        return ["oci", *args]

    async def run_oci_cli(self, command: str) -> CLIResult:
        """OCI CLIコマンドを実行する。

        Args:
            command: OCI CLIコマンド文字列。

        Returns:
            CLI実行結果。

        Raises:
            CommandNotAllowedError: コマンドがホワイトリスト外の場合。
        """
        args = self._validate_oci_command(command)

        exit_code, stdout, stderr = await self._run_subprocess(args)

        return CLIResult(
            success=exit_code == 0,
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
        )

    async def oci_sdk_call(self, service: str, operation: str, params: dict[str, object]) -> dict[str, object]:
        """OCI SDK for Pythonを利用した構造化API呼び出し。

        現フェーズではOCI SDKクライアント未統合のため、エラーを返す。

        Args:
            service: OCIサービス名。
            operation: 操作名。
            params: パラメータ。

        Returns:
            構造化されたエラーレスポンス。
        """
        return {
            "error": "NotImplemented",
            "message": "OCI SDK call is not yet implemented. Use run_oci_cli for OCI operations.",
            "service": service,
            "operation": operation,
        }

    async def create_rm_stack(self, session_id: str, compartment_id: str, terraform_dir: str) -> dict[str, object]:
        """Resource Managerスタックを作成する。

        現フェーズではOCI SDKクライアント未統合のため、エラーを返す。

        Args:
            session_id: セッションID。
            compartment_id: コンパートメントOCID。
            terraform_dir: Terraformファイルのディレクトリ。

        Returns:
            構造化されたエラーレスポンス。
        """
        return {
            "error": "NotImplemented",
            "message": (
                "Resource Manager integration is not yet implemented. Use run_terraform_plan/apply for local execution."
            ),
        }

    async def run_rm_plan(self, stack_id: str) -> dict[str, object]:
        """Resource Manager Planジョブを実行する。

        現フェーズではOCI SDKクライアント未統合のため、エラーを返す。
        """
        return {
            "error": "NotImplemented",
            "message": "Resource Manager integration is not yet implemented.",
        }

    async def run_rm_apply(self, stack_id: str) -> dict[str, object]:
        """Resource Manager Applyジョブを実行する。

        現フェーズではOCI SDKクライアント未統合のため、エラーを返す。
        """
        return {
            "error": "NotImplemented",
            "message": "Resource Manager integration is not yet implemented.",
        }

    async def get_rm_job_status(self, job_id: str) -> dict[str, object]:
        """Resource Managerジョブの状態を取得する。

        現フェーズではOCI SDKクライアント未統合のため、エラーを返す。
        """
        return {
            "error": "NotImplemented",
            "message": "Resource Manager integration is not yet implemented.",
        }
