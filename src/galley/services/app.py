"""アプリケーションのテンプレート管理・デプロイを行うサービス。"""

from __future__ import annotations

import asyncio
import fnmatch
import json
import os
import shutil
import tarfile
import tempfile
import time
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from galley.models.app import AppStatus, DeployResult, TemplateMetadata
from galley.models.errors import (
    AppNotScaffoldedError,
    ArchitectureNotFoundError,
    ProtectedFileError,
    TemplateNotFoundError,
)
from galley.storage.service import StorageService

if TYPE_CHECKING:
    from galley.config import ServerConfig

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

    def __init__(
        self,
        storage: StorageService,
        config_dir: Path,
        config: ServerConfig | None = None,
    ) -> None:
        self._storage = storage
        self._config_dir = config_dir
        self._templates_dir = config_dir / "templates"
        self._config = config

    def _app_dir(self, session_id: str) -> Path:
        """セッションのアプリケーションディレクトリを返す。"""
        session_dir = self._storage.get_session_dir(session_id)
        return session_dir / "app"

    def _snapshots_dir(self, session_id: str) -> Path:
        """セッションのスナップショットディレクトリを返す。"""
        session_dir = self._storage.get_session_dir(session_id)
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

    def _k8s_dir(self, session_id: str) -> Path:
        """セッションのK8sマニフェストディレクトリを返す。"""
        session_dir = self._storage.get_session_dir(session_id)
        return session_dir / "k8s"

    def _kubeconfig_path(self, session_id: str) -> Path:
        """セッションのkubeconfigファイルパスを返す。"""
        session_dir = self._storage.get_session_dir(session_id)
        return session_dir / "kubeconfig"

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

    def _get_app_name(self, session_id: str) -> str:
        """セッションのアプリ名を取得する（テンプレートメタデータまたはセッションIDから）。"""
        metadata_file = self._app_dir(session_id).parent / "template-metadata.json"
        if metadata_file.exists():
            try:
                data = json.loads(metadata_file.read_text(encoding="utf-8"))
                return str(data.get("name", f"galley-app-{session_id[:8]}"))
            except (json.JSONDecodeError, ValueError):
                pass
        return f"galley-app-{session_id[:8]}"

    def _get_app_port(self, session_id: str) -> int:
        """セッションのアプリポートを取得する（デフォルト: 8000）。"""
        app_dir = self._app_dir(session_id)
        # Dockerfileからポートを推定
        dockerfile = app_dir / "Dockerfile"
        if dockerfile.exists():
            content = dockerfile.read_text(encoding="utf-8")
            for line in content.splitlines():
                stripped = line.strip()
                if stripped.startswith("EXPOSE"):
                    parts = stripped.split()
                    if len(parts) >= 2:
                        try:
                            return int(parts[1])
                        except ValueError:
                            pass
        return 8000

    def _generate_k8s_manifests(
        self,
        session_id: str,
        image_uri: str,
        namespace: str = "default",
    ) -> Path:
        """K8sマニフェスト（Deployment + Service）を生成する。

        Args:
            session_id: セッションID。
            image_uri: コンテナイメージURI。
            namespace: K8s名前空間。

        Returns:
            マニフェストが保存されたディレクトリのパス。
        """
        app_name = self._get_app_name(session_id)
        app_port = self._get_app_port(session_id)
        k8s_dir = self._k8s_dir(session_id)
        k8s_dir.mkdir(parents=True, exist_ok=True)

        deployment_yaml = f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {app_name}
  namespace: {namespace}
  labels:
    app: {app_name}
    managed-by: galley
spec:
  replicas: 1
  selector:
    matchLabels:
      app: {app_name}
  template:
    metadata:
      labels:
        app: {app_name}
    spec:
      containers:
        - name: {app_name}
          image: {image_uri}
          ports:
            - containerPort: {app_port}
"""

        service_yaml = f"""apiVersion: v1
kind: Service
metadata:
  name: {app_name}
  namespace: {namespace}
  labels:
    app: {app_name}
    managed-by: galley
spec:
  type: LoadBalancer
  selector:
    app: {app_name}
  ports:
    - port: 80
      targetPort: {app_port}
      protocol: TCP
"""

        (k8s_dir / "deployment.yaml").write_text(deployment_yaml, encoding="utf-8")
        (k8s_dir / "service.yaml").write_text(service_yaml, encoding="utf-8")

        return k8s_dir

    async def _setup_kubeconfig(self, session_id: str, cluster_id: str) -> Path:
        """OKEクラスタのkubeconfigを取得する。

        Args:
            session_id: セッションID。
            cluster_id: OKEクラスタのOCID。

        Returns:
            kubeconfigファイルのパス。

        Raises:
            RuntimeError: kubeconfig取得に失敗した場合。
        """
        kubeconfig = self._kubeconfig_path(session_id)
        kubeconfig.parent.mkdir(parents=True, exist_ok=True)

        args = [
            "oci",
            "ce",
            "cluster",
            "create-kubeconfig",
            "--cluster-id",
            cluster_id,
            "--file",
            str(kubeconfig),
            "--token-version",
            "2.0.0",
        ]
        # Container Instance環境ではResourcePrincipal認証を使用
        if os.environ.get("OCI_RESOURCE_PRINCIPAL_VERSION"):
            args.insert(1, "--auth")
            args.insert(2, "resource_principal")

        exit_code, _stdout, stderr = await self._run_subprocess(args)
        if exit_code != 0:
            raise RuntimeError(f"Failed to get kubeconfig: {stderr}")

        return kubeconfig

    # ----------------------------------------------------------------
    # Docker イメージビルド (Build Instance 経由)
    # ----------------------------------------------------------------

    async def _upload_app_tarball(self, session_id: str) -> str:
        """アプリケーションコードを tar.gz にして Object Storage にアップロードする。

        Args:
            session_id: セッションID。

        Returns:
            Object Storage 上のオブジェクト名。

        Raises:
            RuntimeError: アップロードに失敗した場合。
        """
        app_dir = self._app_dir(session_id)
        object_name = f"builds/{session_id}/app.tar.gz"

        with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            with tarfile.open(tmp_path, "w:gz") as tar:
                tar.add(str(app_dir), arcname=".")

            config = self._config
            if not config or not config.bucket_name or not config.bucket_namespace:
                raise RuntimeError("Object Storage configuration is not set")

            auth_args = ["--auth", "resource_principal"] if os.environ.get("OCI_RESOURCE_PRINCIPAL_VERSION") else []
            args = [
                "oci",
                *auth_args,
                "os",
                "object",
                "put",
                "--bucket-name",
                config.bucket_name,
                "--namespace",
                config.bucket_namespace,
                "--name",
                object_name,
                "--file",
                tmp_path,
                "--force",
            ]

            exit_code, _stdout, stderr = await self._run_subprocess(args)
            if exit_code != 0:
                raise RuntimeError(f"Failed to upload app tarball: {stderr}")

            return object_name
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    async def _build_and_push_image(
        self,
        session_id: str,
        app_name: str,
    ) -> str:
        """Build Instance 上で Docker イメージをビルドし OCIR にプッシュする。

        Args:
            session_id: セッションID。
            app_name: アプリケーション名（イメージタグに使用）。

        Returns:
            プッシュされたイメージの URI。

        Raises:
            RuntimeError: ビルド設定が不足、またはビルドに失敗した場合。
        """
        config = self._config
        if not config:
            raise RuntimeError("Server configuration is not set")
        if not config.build_instance_id:
            raise RuntimeError("GALLEY_BUILD_INSTANCE_ID is not configured")
        if not config.ocir_endpoint or not config.ocir_username or not config.ocir_auth_token:
            raise RuntimeError("OCIR credentials are not configured")

        # 1. app code を Object Storage にアップロード
        object_name = await self._upload_app_tarball(session_id)

        # 2. イメージ URI を組み立て
        namespace = config.bucket_namespace
        image_uri = f"{config.ocir_endpoint}/{namespace}/{app_name}:{session_id[:8]}"

        # 3. ビルドスクリプトを組み立て
        build_script = self._build_script(
            bucket_name=config.bucket_name,
            bucket_namespace=config.bucket_namespace,
            object_name=object_name,
            image_uri=image_uri,
            ocir_endpoint=config.ocir_endpoint,
            ocir_username=config.ocir_username,
            ocir_auth_token=config.ocir_auth_token,
        )

        # 4. instance-agent command create でビルド実行
        compartment_id = os.environ.get(
            "GALLEY_WORK_COMPARTMENT_ID",
            os.environ.get("OCI_COMPARTMENT_ID", ""),
        )
        if not compartment_id:
            raise RuntimeError("Compartment ID is not configured. Set GALLEY_WORK_COMPARTMENT_ID environment variable.")

        content_json = json.dumps({"source": {"sourceType": "TEXT", "text": build_script}})
        target_json = json.dumps({"instanceId": config.build_instance_id})

        auth_args = ["--auth", "resource_principal"] if os.environ.get("OCI_RESOURCE_PRINCIPAL_VERSION") else []
        args = [
            "oci",
            *auth_args,
            "instance-agent",
            "command",
            "create",
            "--compartment-id",
            compartment_id,
            "--timeout-in-seconds",
            "600",
            "--content",
            content_json,
            "--target",
            target_json,
        ]

        exit_code, stdout, stderr = await self._run_subprocess(args)
        if exit_code != 0:
            raise RuntimeError(f"Failed to create build command: {stderr}")

        # command ID を取得
        try:
            result = json.loads(stdout)
            command_id = result["data"]["id"]
        except (json.JSONDecodeError, KeyError) as e:
            raise RuntimeError(f"Failed to parse command create response: {e}") from e

        # 5. コマンド完了を待機
        cmd_exit_code, output = await self._wait_for_command(command_id, config.build_instance_id)
        if cmd_exit_code != 0:
            raise RuntimeError(f"Docker build failed (exit={cmd_exit_code}): {output}")

        return image_uri

    @staticmethod
    def _build_script(
        *,
        bucket_name: str,
        bucket_namespace: str,
        object_name: str,
        image_uri: str,
        ocir_endpoint: str,
        ocir_username: str,
        ocir_auth_token: str,
    ) -> str:
        """Build Instance 上で実行するビルドスクリプトを生成する。"""
        import base64

        # トークンをbase64エンコードしてシェルインジェクションを防止
        token_b64 = base64.b64encode(ocir_auth_token.encode()).decode()

        return f"""#!/bin/bash
set -e
cd /opt/galley-build
rm -rf app && mkdir app

# Download app code from Object Storage
oci os object get \\
  --auth instance_principal \\
  --bucket-name {bucket_name} \\
  --namespace {bucket_namespace} \\
  --name {object_name} \\
  --file app.tar.gz

tar xzf app.tar.gz -C app
cd app

# Build Docker image
docker build -t {image_uri} .

# Login and push to OCIR (token is base64 encoded to prevent injection)
echo {token_b64} | base64 -d | docker login {ocir_endpoint} -u '{ocir_username}' --password-stdin
docker push {image_uri}

echo "BUILD_SUCCESS"
"""

    async def _wait_for_command(
        self,
        command_id: str,
        instance_id: str,
        poll_interval: float = 10.0,
        max_wait: float = 600.0,
    ) -> tuple[int, str]:
        """instance-agent コマンドの完了をポーリングで待機する。

        Args:
            command_id: コマンドのOCID。
            instance_id: インスタンスのOCID。
            poll_interval: ポーリング間隔（秒）。
            max_wait: 最大待機時間（秒）。

        Returns:
            (exit_code, output) のタプル。
        """
        auth_args = ["--auth", "resource_principal"] if os.environ.get("OCI_RESOURCE_PRINCIPAL_VERSION") else []
        start = time.monotonic()

        while time.monotonic() - start < max_wait:
            args = [
                "oci",
                *auth_args,
                "instance-agent",
                "command-execution",
                "get",
                "--command-id",
                command_id,
                "--instance-id",
                instance_id,
            ]
            exit_code, stdout, _stderr = await self._run_subprocess(args)
            if exit_code != 0:
                await asyncio.sleep(poll_interval)
                continue

            try:
                data = json.loads(stdout)
                state = data["data"]["lifecycle-state"]
            except (json.JSONDecodeError, KeyError):
                await asyncio.sleep(poll_interval)
                continue

            if state in ("SUCCEEDED", "FAILED", "CANCELED", "TIMED_OUT"):
                cmd_exit_code = data["data"].get("content", {}).get("exit-code", -1)
                output_text = data["data"].get("content", {}).get("output", {}).get("text", "")
                return (cmd_exit_code, output_text)

            await asyncio.sleep(poll_interval)

        return (-1, "Build timed out")

    async def build_and_deploy(
        self,
        session_id: str,
        cluster_id: str,
        image_uri: str | None = None,
        namespace: str = "default",
    ) -> DeployResult:
        """OKEクラスタにアプリケーションをデプロイする。

        K8sマニフェスト（Deployment + Service）を自動生成し、
        kubectl applyでデプロイを実行する。
        image_uri が未指定の場合、Build Instance でビルド・OCIR プッシュを行う。

        Args:
            session_id: セッションID。
            cluster_id: OKEクラスタのOCID。
            image_uri: コンテナイメージURI（未指定時はビルドを実行）。
            namespace: K8s名前空間。

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

        app_name = self._get_app_name(session_id)

        # 0. image_uri が未指定の場合、Build Instance でビルド
        if not image_uri:
            try:
                image_uri = await self._build_and_push_image(session_id, app_name)
            except RuntimeError as e:
                return DeployResult(
                    success=False,
                    reason=f"Image build failed: {e}",
                )

        # 1. K8sマニフェスト生成
        k8s_dir = self._generate_k8s_manifests(session_id, image_uri, namespace)

        # 2. kubeconfig取得
        try:
            kubeconfig = await self._setup_kubeconfig(session_id, cluster_id)
        except RuntimeError as e:
            return DeployResult(
                success=False,
                image_uri=image_uri,
                reason=str(e),
                k8s_manifests_dir=str(k8s_dir),
            )

        # 3. kubectl apply
        exit_code, stdout, stderr = await self._run_subprocess(
            ["kubectl", "apply", "-f", str(k8s_dir), "--kubeconfig", str(kubeconfig)]
        )
        if exit_code != 0:
            return DeployResult(
                success=False,
                image_uri=image_uri,
                reason=f"kubectl apply failed: {stderr}",
                k8s_manifests_dir=str(k8s_dir),
            )

        # 4. rollout status (タイムアウト300秒)
        exit_code, stdout, stderr = await self._run_subprocess(
            [
                "kubectl",
                "rollout",
                "status",
                f"deployment/{app_name}",
                "--kubeconfig",
                str(kubeconfig),
                "--namespace",
                namespace,
                "--timeout",
                "300s",
            ]
        )
        if exit_code != 0:
            return DeployResult(
                success=False,
                image_uri=image_uri,
                reason=f"Deployment rollout failed: {stderr or stdout}",
                k8s_manifests_dir=str(k8s_dir),
            )

        # 5. エンドポイント取得（LoadBalancer IP）
        endpoint: str | None = None
        exit_code, stdout, stderr = await self._run_subprocess(
            [
                "kubectl",
                "get",
                "svc",
                app_name,
                "--kubeconfig",
                str(kubeconfig),
                "--namespace",
                namespace,
                "-o",
                "jsonpath={.status.loadBalancer.ingress[0].ip}",
            ]
        )
        if exit_code == 0 and stdout.strip():
            endpoint = f"http://{stdout.strip()}"

        return DeployResult(
            success=True,
            image_uri=image_uri,
            endpoint=endpoint,
            k8s_manifests_dir=str(k8s_dir),
        )

    async def check_app_status(self, session_id: str) -> AppStatus:
        """アプリケーションのデプロイ状態を確認する。

        kubeconfigが存在する場合、kubectlでデプロイ状態を確認する。

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

        kubeconfig = self._kubeconfig_path(session_id)
        if not kubeconfig.exists():
            return AppStatus(session_id=session_id, status="not_deployed")

        app_name = self._get_app_name(session_id)

        # デプロイメント状態を確認
        exit_code, stdout, _stderr = await self._run_subprocess(
            [
                "kubectl",
                "get",
                "deployment",
                app_name,
                "--kubeconfig",
                str(kubeconfig),
                "-o",
                "jsonpath={.status.readyReplicas}",
            ]
        )

        if exit_code != 0:
            return AppStatus(session_id=session_id, status="not_deployed")

        ready_replicas = stdout.strip()
        status: Literal["deploying", "running"] = (
            "deploying" if not ready_replicas or ready_replicas == "0" else "running"
        )

        # エンドポイント取得
        endpoint: str | None = None
        exit_code, stdout, _stderr = await self._run_subprocess(
            [
                "kubectl",
                "get",
                "svc",
                app_name,
                "--kubeconfig",
                str(kubeconfig),
                "-o",
                "jsonpath={.status.loadBalancer.ingress[0].ip}",
            ]
        )
        if exit_code == 0 and stdout.strip():
            endpoint = f"http://{stdout.strip()}"

        return AppStatus(
            session_id=session_id,
            status=status,
            endpoint=endpoint,
        )
