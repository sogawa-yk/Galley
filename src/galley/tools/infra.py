"""インフラ層のMCPツール定義。"""

from typing import Any

from fastmcp import FastMCP

from galley.models.errors import GalleyError
from galley.services.infra import InfraService


def register_infra_tools(mcp: FastMCP, infra_service: InfraService) -> None:
    """インフラ関連のMCPツールを登録する。"""

    @mcp.tool()
    async def run_terraform_plan(session_id: str, terraform_dir: str) -> dict[str, Any]:
        """Terraform planを実行する。

        指定されたディレクトリでterraform planを実行し、結果を返します。
        LLMがエラーメッセージを解析してTerraformコードを修正→再実行する
        自動デバッグループに使用します。

        Args:
            session_id: セッションID。
            terraform_dir: Terraformファイルが格納されたディレクトリパス。
        """
        try:
            result = await infra_service.run_terraform_plan(session_id, terraform_dir)
            return result.model_dump()
        except (GalleyError, ValueError) as e:
            return {"error": type(e).__name__, "message": str(e)}

    @mcp.tool()
    async def run_terraform_apply(session_id: str, terraform_dir: str) -> dict[str, Any]:
        """Terraform applyを実行する。

        指定されたディレクトリでterraform apply -auto-approveを実行し、
        OCIリソースをプロビジョニングします。

        Args:
            session_id: セッションID。
            terraform_dir: Terraformファイルが格納されたディレクトリパス。
        """
        try:
            result = await infra_service.run_terraform_apply(session_id, terraform_dir)
            return result.model_dump()
        except (GalleyError, ValueError) as e:
            return {"error": type(e).__name__, "message": str(e)}

    @mcp.tool()
    async def run_terraform_destroy(session_id: str, terraform_dir: str) -> dict[str, Any]:
        """Terraform destroyを実行する。

        指定されたディレクトリでterraform destroy -auto-approveを実行し、
        プロビジョニング済みのOCIリソースをクリーンアップします。

        Args:
            session_id: セッションID。
            terraform_dir: Terraformファイルが格納されたディレクトリパス。
        """
        try:
            result = await infra_service.run_terraform_destroy(session_id, terraform_dir)
            return result.model_dump()
        except (GalleyError, ValueError) as e:
            return {"error": type(e).__name__, "message": str(e)}

    @mcp.tool()
    async def run_oci_cli(command: str) -> dict[str, Any]:
        """OCI CLIコマンドを実行する。

        OCI CLIコマンドを実行し、結果を返します。
        セキュリティのため、許可されたサービスコマンドのみ実行可能です。

        Args:
            command: OCI CLIコマンド文字列（例: "oci compute instance list --compartment-id ..."）。
        """
        try:
            result = await infra_service.run_oci_cli(command)
            return result.model_dump()
        except GalleyError as e:
            return {"error": type(e).__name__, "message": str(e)}

    @mcp.tool()
    async def oci_sdk_call(
        service: str,
        operation: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """OCI SDK for Pythonを利用した構造化API呼び出し。

        OCI SDKを使用して構造化されたAPI呼び出しを実行します。
        現在は未実装です。OCI操作にはrun_oci_cliを使用してください。

        Args:
            service: OCIサービス名（例: "compute", "network"）。
            operation: 操作名（例: "list_instances", "get_vcn"）。
            params: APIパラメータ（任意）。
        """
        result = await infra_service.oci_sdk_call(service, operation, params or {})
        return dict(result)

    @mcp.tool()
    async def create_rm_stack(
        session_id: str,
        compartment_id: str,
        terraform_dir: str,
    ) -> dict[str, Any]:
        """Resource Managerスタックを作成する。

        OCI Resource Managerにスタックを作成し、Terraformコードをアップロードします。
        現在は未実装です。ローカルTerraform実行を使用してください。

        Args:
            session_id: セッションID。
            compartment_id: コンパートメントOCID。
            terraform_dir: Terraformファイルのディレクトリパス。
        """
        result = await infra_service.create_rm_stack(session_id, compartment_id, terraform_dir)
        return dict(result)

    @mcp.tool()
    async def run_rm_plan(stack_id: str) -> dict[str, Any]:
        """Resource Manager Planジョブを実行する。

        指定されたスタックでPlanジョブを実行します。
        現在は未実装です。ローカルTerraform実行を使用してください。

        Args:
            stack_id: Resource ManagerスタックOCID。
        """
        result = await infra_service.run_rm_plan(stack_id)
        return dict(result)

    @mcp.tool()
    async def run_rm_apply(stack_id: str) -> dict[str, Any]:
        """Resource Manager Applyジョブを実行する。

        指定されたスタックでApplyジョブを実行します。
        現在は未実装です。ローカルTerraform実行を使用してください。

        Args:
            stack_id: Resource ManagerスタックOCID。
        """
        result = await infra_service.run_rm_apply(stack_id)
        return dict(result)

    @mcp.tool()
    async def get_rm_job_status(job_id: str) -> dict[str, Any]:
        """Resource Managerジョブの状態を取得する。

        指定されたジョブの実行状態とログを取得します。
        現在は未実装です。

        Args:
            job_id: ジョブOCID。
        """
        result = await infra_service.get_rm_job_status(job_id)
        return dict(result)
