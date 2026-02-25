"""インフラストラクチャの構築・管理を行うサービス。"""

import asyncio
import base64
import io
import os
import re
import shlex
import zipfile
from pathlib import Path
from typing import Any

import oci

from galley.models.errors import (
    ArchitectureNotFoundError,
    CommandNotAllowedError,
    InfraOperationInProgressError,
)
from galley.models.infra import CLIResult, RMJob, TerraformCommand, TerraformErrorDetail, TerraformResult
from galley.storage.service import StorageService

# terraform_dirで禁止するパスパターン
_DISALLOWED_PATH_PATTERNS = ("..", "~")

# RM自動入力変数（これらはvariablesから除外してRMに任せる）
_RM_AUTO_VARIABLES = frozenset({"region", "compartment_ocid", "tenancy_ocid", "current_user_ocid"})

# ジョブポーリング間隔（秒）
_JOB_POLL_INTERVAL = 5

# ジョブタイムアウト（秒）
_JOB_TIMEOUT_PLAN = 300  # 5分
_JOB_TIMEOUT_APPLY_DESTROY = 1800  # 30分


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

# Terraformエラーメッセージのパース用正規表現
# "Error: <message>\n\n  on <file> line <line>:" の形式
_TF_ERROR_RE = re.compile(
    r"Error:\s*(?P<message>[^\n]+)(?:\n\n\s+on\s+(?P<file>\S+)\s+line\s+(?P<line>\d+))?",
    re.MULTILINE,
)


class InfraService:
    """インフラストラクチャの構築・管理を行う。"""

    def __init__(self, storage: StorageService, config_dir: Path) -> None:
        self._storage = storage
        self._config_dir = config_dir
        # セッション単位の排他ロック
        self._session_locks: dict[str, asyncio.Lock] = {}
        # RMクライアント（遅延初期化）
        self._rm_client: oci.resource_manager.ResourceManagerClient | None = None

    def _get_session_lock(self, session_id: str) -> asyncio.Lock:
        """セッション単位のasyncio.Lockを取得する。"""
        if session_id not in self._session_locks:
            self._session_locks[session_id] = asyncio.Lock()
        return self._session_locks[session_id]

    def _get_rm_client(self) -> oci.resource_manager.ResourceManagerClient:
        """RMクライアントを遅延初期化して返す。"""
        if self._rm_client is None:
            if os.environ.get("OCI_RESOURCE_PRINCIPAL_VERSION"):
                signer = oci.auth.signers.get_resource_principals_signer()
                self._rm_client = oci.resource_manager.ResourceManagerClient({}, signer=signer)
            else:
                config = oci.config.from_file()
                self._rm_client = oci.resource_manager.ResourceManagerClient(config)
        return self._rm_client

    @staticmethod
    def _zip_terraform_dir(terraform_dir: Path) -> str:
        """Terraformディレクトリをzip化してbase64エンコード文字列を返す。

        .terraform/ と *.tfstate* ファイルを除外する。
        """
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for file_path in terraform_dir.rglob("*"):
                if not file_path.is_file():
                    continue
                rel = file_path.relative_to(terraform_dir)
                # .terraform/ ディレクトリと tfstate ファイルを除外
                parts = rel.parts
                if any(p == ".terraform" for p in parts):
                    continue
                if "tfstate" in file_path.name:
                    continue
                zf.write(file_path, str(rel))
        return base64.b64encode(buf.getvalue()).decode("ascii")

    def _get_tenancy_ocid(self) -> str:
        """テナンシーOCIDを取得する。"""
        if os.environ.get("OCI_RESOURCE_PRINCIPAL_VERSION"):
            signer = oci.auth.signers.get_resource_principals_signer()
            return str(signer.tenancy_id)
        else:
            config = oci.config.from_file()
            return str(config.get("tenancy", ""))

    def _build_rm_variables(self, variables: dict[str, str] | None) -> dict[str, str]:
        """RM用変数を構築する。

        ユーザー指定変数にregion/compartment_ocid/tenancy_ocidを自動設定する。
        ユーザーが明示的に指定した場合はそちらを優先する。
        """
        result = dict(variables) if variables else {}
        if "region" not in result:
            result["region"] = os.environ.get("GALLEY_REGION", "")
        if "compartment_ocid" not in result:
            result["compartment_ocid"] = os.environ.get("GALLEY_WORK_COMPARTMENT_ID", "")
        if "tenancy_ocid" not in result:
            try:
                result["tenancy_ocid"] = self._get_tenancy_ocid()
            except Exception:
                result["tenancy_ocid"] = ""
        return result

    async def _ensure_rm_stack(
        self,
        session_id: str,
        terraform_dir: Path,
        variables: dict[str, str] | None = None,
    ) -> str:
        """RMスタックを作成または更新し、stack_idを返す。"""
        session = await self._storage.load_session(session_id)
        client = self._get_rm_client()

        zip_content = self._zip_terraform_dir(terraform_dir)
        filtered_vars = self._build_rm_variables(variables)

        # コンパートメントIDの取得
        compartment_id = os.environ.get("GALLEY_WORK_COMPARTMENT_ID", "")
        if not compartment_id and variables:
            compartment_id = variables.get("compartment_ocid", "")

        if session.rm_stack_id:
            # スタック更新
            update_details = oci.resource_manager.models.UpdateStackDetails(
                display_name=f"galley-{session_id}",
                config_source=oci.resource_manager.models.UpdateZipUploadConfigSourceDetails(
                    zip_file_base64_encoded=zip_content,
                ),
                variables=filtered_vars,
            )
            await asyncio.to_thread(
                client.update_stack,
                session.rm_stack_id,
                update_details,
            )
            return session.rm_stack_id
        else:
            # スタック新規作成
            create_details = oci.resource_manager.models.CreateStackDetails(
                compartment_id=compartment_id,
                display_name=f"galley-{session_id}",
                config_source=oci.resource_manager.models.CreateZipUploadConfigSourceDetails(
                    zip_file_base64_encoded=zip_content,
                ),
                variables=filtered_vars,
                terraform_version="1.5.x",
            )
            response = await asyncio.to_thread(
                client.create_stack,
                create_details,
            )
            stack_id: str = response.data.id
            # セッションにstack_idを保存
            session.rm_stack_id = stack_id
            await self._storage.save_session(session)
            return stack_id

    async def _run_rm_job(
        self,
        stack_id: str,
        operation: str,
        command: TerraformCommand,
    ) -> TerraformResult:
        """RMジョブを作成・ポーリング・ログ取得してTerraformResultを返す。"""
        client = self._get_rm_client()

        # ジョブ作成（operation別のOperationDetailsサブクラスを使用）
        rm_models = oci.resource_manager.models
        if operation == "PLAN":
            op_details = rm_models.CreatePlanJobOperationDetails()
        elif operation == "APPLY":
            op_details = rm_models.CreateApplyJobOperationDetails(
                execution_plan_strategy="AUTO_APPROVED",
            )
        else:  # DESTROY
            op_details = rm_models.CreateDestroyJobOperationDetails(
                execution_plan_strategy="AUTO_APPROVED",
            )

        create_job_details = rm_models.CreateJobDetails(
            stack_id=stack_id,
            job_operation_details=op_details,
        )
        response = await asyncio.to_thread(client.create_job, create_job_details)
        job_id: str = response.data.id

        # ポーリング
        timeout = _JOB_TIMEOUT_PLAN if operation == "PLAN" else _JOB_TIMEOUT_APPLY_DESTROY
        elapsed = 0
        lifecycle_state = ""
        while elapsed < timeout:
            await asyncio.sleep(_JOB_POLL_INTERVAL)
            elapsed += _JOB_POLL_INTERVAL
            job_response = await asyncio.to_thread(client.get_job, job_id)
            lifecycle_state = job_response.data.lifecycle_state
            if lifecycle_state in ("SUCCEEDED", "FAILED", "CANCELED"):
                break

        # ログ取得（get_job_logs_contentで生ログテキストを取得）
        stdout = ""
        try:
            logs_response = await asyncio.to_thread(client.get_job_logs_content, job_id)
            stdout = logs_response.data.text if hasattr(logs_response.data, "text") else str(logs_response.data)
        except Exception:
            stdout = f"(Failed to retrieve job logs for {job_id})"

        # タイムアウトチェック
        if lifecycle_state not in ("SUCCEEDED", "FAILED", "CANCELED"):
            return TerraformResult(
                success=False,
                command=command,
                stdout=stdout,
                stderr=f"Job timed out after {timeout}s. Job ID: {job_id}",
                exit_code=1,
            )

        success = lifecycle_state == "SUCCEEDED"
        plan_summary = self._extract_plan_summary(stdout) if success and command == "plan" else None
        errors = self._parse_terraform_errors(stdout) if not success else None

        return TerraformResult(
            success=success,
            command=command,
            stdout=stdout,
            stderr="" if success else f"Job {lifecycle_state}. Job ID: {job_id}",
            exit_code=0 if success else 1,
            plan_summary=plan_summary,
            errors=errors,
        )

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

    @staticmethod
    def _parse_terraform_errors(stderr: str) -> list[TerraformErrorDetail] | None:
        """Terraformのstderrから構造化エラーリストを抽出する。"""
        matches = list(_TF_ERROR_RE.finditer(stderr))
        if not matches:
            return None
        errors: list[TerraformErrorDetail] = []
        for m in matches:
            line_str = m.group("line")
            errors.append(
                TerraformErrorDetail(
                    file=m.group("file"),
                    line=int(line_str) if line_str else None,
                    message=m.group("message").strip(),
                )
            )
        return errors

    def _extract_plan_summary(self, stdout: str) -> str | None:
        """Terraform plan出力からサマリー行を抽出する。"""
        match = _PLAN_SUMMARY_RE.search(stdout)
        if match:
            return match.group(1)
        # "No changes" のケースも検出
        if "No changes" in stdout or "no changes" in stdout.lower():
            return "No changes. Infrastructure is up-to-date."
        return None

    async def run_terraform_plan(
        self,
        session_id: str,
        terraform_dir: str,
        variables: dict[str, str] | None = None,
    ) -> TerraformResult:
        """OCI Resource Manager経由でTerraform planを実行する。

        Terraformファイルをzip化してRMスタックにアップロードし、
        Planジョブを実行して結果を返す。

        Args:
            session_id: セッションID。
            terraform_dir: Terraformファイルが格納されたディレクトリパス。
            variables: Terraform変数。RM自動入力変数(region, compartment_ocid等)は自動除外される。

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
            try:
                stack_id = await self._ensure_rm_stack(session_id, validated_dir, variables)
                return await self._run_rm_job(stack_id, "PLAN", "plan")
            except Exception as e:
                return TerraformResult(
                    success=False,
                    command="plan",
                    stdout="",
                    stderr=str(e),
                    exit_code=1,
                )

    async def run_terraform_apply(
        self,
        session_id: str,
        terraform_dir: str,
        variables: dict[str, str] | None = None,
    ) -> TerraformResult:
        """OCI Resource Manager経由でTerraform applyを実行する。

        Terraformファイルをzip化してRMスタックを更新し、
        Applyジョブ（AUTO_APPROVED）を実行して結果を返す。

        Args:
            session_id: セッションID。
            terraform_dir: Terraformファイルが格納されたディレクトリパス。
            variables: Terraform変数。RM自動入力変数は自動除外される。

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
            try:
                stack_id = await self._ensure_rm_stack(session_id, validated_dir, variables)
                return await self._run_rm_job(stack_id, "APPLY", "apply")
            except Exception as e:
                return TerraformResult(
                    success=False,
                    command="apply",
                    stdout="",
                    stderr=str(e),
                    exit_code=1,
                )

    async def run_terraform_destroy(
        self,
        session_id: str,
        terraform_dir: str,
        variables: dict[str, str] | None = None,
    ) -> TerraformResult:
        """OCI Resource Manager経由でTerraform destroyを実行する。

        RMスタックのDestroyジョブ（AUTO_APPROVED）を実行して結果を返す。

        Args:
            session_id: セッションID。
            terraform_dir: Terraformファイルが格納されたディレクトリパス。
            variables: Terraform変数。RM自動入力変数は自動除外される。

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
            try:
                stack_id = await self._ensure_rm_stack(session_id, validated_dir, variables)
                return await self._run_rm_job(stack_id, "DESTROY", "destroy")
            except Exception as e:
                return TerraformResult(
                    success=False,
                    command="destroy",
                    stdout="",
                    stderr=str(e),
                    exit_code=1,
                )

    async def get_rm_job_status(self, job_id: str) -> dict[str, Any]:
        """Resource Managerジョブの状態とログを取得する。

        Args:
            job_id: ジョブOCID。

        Returns:
            ジョブ状態とログを含む辞書。
        """
        try:
            client = self._get_rm_client()
            job_response = await asyncio.to_thread(client.get_job, job_id)
            job_data = job_response.data

            # ログ取得
            log_text = ""
            try:
                logs_response = await asyncio.to_thread(client.get_job_logs_content, job_id)
                log_text = logs_response.data.text if hasattr(logs_response.data, "text") else str(logs_response.data)
            except Exception:
                log_text = "(Failed to retrieve logs)"

            job = RMJob(
                id=job_data.id,
                stack_id=job_data.stack_id,
                operation=job_data.operation,
                lifecycle_state=job_data.lifecycle_state,
            )
            return {
                "job": job.model_dump(),
                "logs": log_text,
            }
        except Exception as e:
            return {"error": type(e).__name__, "message": str(e)}

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
        # Container Instance環境ではResourcePrincipal認証を使用
        base = ["oci"]
        if os.environ.get("OCI_RESOURCE_PRINCIPAL_VERSION"):
            base.extend(["--auth", "resource_principal"])
        return [*base, *args]

    _OCI_CONFIG_HINT = (
        "OCI CLI is not configured. To set up:\n"
        "1. API Key auth: Run 'oci setup config' to create ~/.oci/config\n"
        "2. Resource Principal: Set OCI_RESOURCE_PRINCIPAL_VERSION env var (for Container Instances)\n"
        "See: https://docs.oracle.com/en-us/iaas/Content/API/Concepts/sdkconfig.htm"
    )

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

        # OCI CLI設定ファイル未検出のエラーを検知してヒントを付与
        setup_hint: str | None = None
        if exit_code != 0 and ("Could not find config file" in stderr or "ConfigFileNotFound" in stderr):
            setup_hint = self._OCI_CONFIG_HINT

        return CLIResult(
            success=exit_code == 0,
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
            setup_hint=setup_hint,
        )

    async def update_terraform_file(
        self,
        session_id: str,
        file_path: str,
        new_content: str,
    ) -> dict[str, str]:
        """セッションのTerraformファイルを更新する。

        Args:
            session_id: セッションID。
            file_path: terraformディレクトリからの相対パス（例: "components.tf"）。
            new_content: 新しいファイル内容。

        Returns:
            更新されたファイルパスを含む辞書。

        Raises:
            SessionNotFoundError: セッションが存在しない場合。
            ArchitectureNotFoundError: アーキテクチャが未設定の場合。
            ValueError: パスが不正な場合。
        """
        session = await self._storage.load_session(session_id)
        if session.architecture is None:
            raise ArchitectureNotFoundError(session_id)

        # パストラバーサル防止
        if ".." in file_path or file_path.startswith("/"):
            raise ValueError(f"Invalid file_path: must be a relative path without '..': {file_path}")

        terraform_dir = self._storage.get_session_dir(session_id) / "terraform"
        target = (terraform_dir / file_path).resolve()

        # terraform_dir 配下であることを確認
        if not str(target).startswith(str(terraform_dir.resolve())):
            raise ValueError(f"Invalid file_path: must be within terraform directory: {file_path}")

        # ディレクトリが存在しない場合はエラー
        if not terraform_dir.exists():
            raise ValueError(f"Terraform directory does not exist for session {session_id}. Run export_iac first.")

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(new_content, encoding="utf-8")

        return {"file_path": str(target), "message": f"File updated: {file_path}"}
