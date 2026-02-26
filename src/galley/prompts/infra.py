"""インフラ層のMCPプロンプト定義。"""

from fastmcp import FastMCP


def register_infra_prompts(mcp: FastMCP) -> None:
    """インフラ関連のMCPプロンプトを登録する。"""

    @mcp.prompt()
    async def oci_resource_check() -> str:
        """OCI CLIでリソース情報を確認するためのプロンプト。

        Terraform apply後のリソース確認や、デバッグ時のリソース調査など、
        許可されたOCI CLIコマンドを使ってOCIリソースの情報を
        確認・調査するフローをガイドします。
        """
        return (
            "OCI CLIを使ってOCIリソースの情報を確認します。\n\n"
            "## 使い方\n\n"
            "`run_oci_cli` ツールにOCI CLIコマンドを渡して実行します。\n\n"
            "## コマンド例\n\n"
            "- `oci compute instance list --compartment-id <OCID>`\n"
            "- `oci network vcn list --compartment-id <OCID>`\n"
            "- `oci db autonomous-database list --compartment-id <OCID>`\n"
            "- `oci oke cluster list --compartment-id <OCID>`\n"
            "- `oci os bucket list --compartment-id <OCID>`\n"
            "- `oci iam compartment list`\n\n"
            "## 注意事項\n\n"
            "- セキュリティのため、許可されたサービスコマンドのみ実行可能です。\n"
            "- 出力がJSON形式の場合、必要なフィールドを抽出して利用者に提示してください。\n"
            "- `--output table` オプションを付けると表形式で見やすい出力が得られます。\n"
        )

    @mcp.prompt()
    async def infra_cleanup(session_id: str) -> str:
        """インフラリソースをクリーンアップするためのプロンプト。

        Terraform destroyによるリソース削除フローをガイドします。

        Args:
            session_id: セッションID。
        """
        return (
            f"セッション `{session_id}` で構築したインフラリソースをクリーンアップします。\n\n"
            "## 手順\n\n"
            "1. `run_terraform_plan` ツールでplanを実行し、削除対象のリソース一覧を確認してください。\n"
            "2. 削除対象のリソースを利用者に提示し、確認を得てください。\n"
            "3. `run_terraform_destroy` ツールでリソースを削除してください。\n\n"
            "## 注意事項\n\n"
            "- destroyは取り消せません。実行前に必ず利用者の確認を得てください。\n"
            "- 削除完了後、`stdout` でリソースが正常に削除されたことを確認してください。\n"
            "- エラーが発生した場合は、`stderr` を分析して原因を特定してください。\n"
        )
