"""インフラ層のMCPツール定義。"""

from typing import Any

from fastmcp import FastMCP

from galley.models.errors import GalleyError
from galley.services.infra import InfraService


def register_infra_tools(mcp: FastMCP, infra_service: InfraService) -> None:
    """インフラ関連のMCPツールを登録する。"""

    @mcp.tool()
    async def run_terraform_plan(
        session_id: str,
        terraform_dir: str,
        variables: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """OCI Resource Manager経由でTerraform planを実行する。

        Terraformファイルをzip化してRMスタックにアップロードし、
        Planジョブを実行して結果を返します。
        RM自動入力変数（region, compartment_ocid等）はvariablesから自動除外されます。

        Args:
            session_id: セッションID。
            terraform_dir: Terraformファイルが格納されたディレクトリパス。
            variables: Terraform変数。RM自動入力変数は自動除外される。
        """
        try:
            result = await infra_service.run_terraform_plan(session_id, terraform_dir, variables)
            return result.model_dump()
        except (GalleyError, ValueError) as e:
            return {"error": type(e).__name__, "message": str(e)}

    @mcp.tool()
    async def run_terraform_apply(
        session_id: str,
        terraform_dir: str,
        variables: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """OCI Resource Manager経由でTerraform applyを実行する。

        RMスタックを更新し、Applyジョブ（自動承認）を実行して
        OCIリソースをプロビジョニングします。

        Args:
            session_id: セッションID。
            terraform_dir: Terraformファイルが格納されたディレクトリパス。
            variables: Terraform変数。RM自動入力変数は自動除外される。
        """
        try:
            result = await infra_service.run_terraform_apply(session_id, terraform_dir, variables)
            return result.model_dump()
        except (GalleyError, ValueError) as e:
            return {"error": type(e).__name__, "message": str(e)}

    @mcp.tool()
    async def run_terraform_destroy(
        session_id: str,
        terraform_dir: str,
        variables: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """OCI Resource Manager経由でTerraform destroyを実行する。

        RMスタックのDestroyジョブ（自動承認）を実行し、
        プロビジョニング済みのOCIリソースをクリーンアップします。

        Args:
            session_id: セッションID。
            terraform_dir: Terraformファイルが格納されたディレクトリパス。
            variables: Terraform変数。RM自動入力変数は自動除外される。
        """
        try:
            result = await infra_service.run_terraform_destroy(session_id, terraform_dir, variables)
            return result.model_dump()
        except (GalleyError, ValueError) as e:
            return {"error": type(e).__name__, "message": str(e)}

    @mcp.tool()
    async def update_terraform_file(
        session_id: str,
        file_path: str,
        new_content: str,
    ) -> dict[str, Any]:
        """セッションのTerraformファイルを更新する。

        export_iacで生成されたTerraformファイルを編集します。
        terraform plan → エラー修正 → 再planのデバッグループに使用します。
        次回のplan/apply時にzip化されてRMにアップロードされます。

        Args:
            session_id: セッションID。
            file_path: terraformディレクトリからの相対パス（例: "components.tf", "variables.tf"）。
            new_content: 新しいファイル内容。
        """
        try:
            result = await infra_service.update_terraform_file(session_id, file_path, new_content)
            return result
        except (GalleyError, ValueError) as e:
            return {"error": type(e).__name__, "message": str(e)}

    @mcp.tool()
    async def run_oci_cli(command: str) -> dict[str, Any]:
        """OCI CLIコマンドを実行する。

        OCI CLIコマンドを実行し、結果を返します。
        セキュリティのため、許可されたサービスコマンドのみ実行可能です。

        認証方式:
        - Container Instance: Resource Principal（自動設定）
        - ローカル開発: API Key（~/.oci/config）。'oci setup config'で設定。

        Args:
            command: OCI CLIコマンド文字列（例: "oci compute instance list --compartment-id ..."）。
        """
        try:
            result = await infra_service.run_oci_cli(command)
            return result.model_dump()
        except GalleyError as e:
            return {"error": type(e).__name__, "message": str(e)}

    @mcp.tool()
    async def get_rm_job_status(job_id: str) -> dict[str, Any]:
        """Resource Managerジョブの状態とログを取得する。

        実行中のジョブの進行状況を確認したり、
        完了済みジョブのログを取得するために使用します。

        Args:
            job_id: ジョブOCID。
        """
        result = await infra_service.get_rm_job_status(job_id)
        return dict(result)
