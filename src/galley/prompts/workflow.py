"""ワークフロー統合MCPプロンプト定義。"""

from fastmcp import FastMCP


def register_workflow_prompts(mcp: FastMCP) -> None:
    """ワークフロー系のMCPプロンプトを登録する。"""

    def _hearing_phase() -> str:
        return (
            "## Phase 1: ヒアリング\n\n"
            "1. `create_session` ツールでセッションを作成してください。\n"
            "2. **作成されたセッションID（`session_id`）を利用者に必ず提示してください。**"
            " セッションIDは以降の全ての操作で必要です。\n"
            "3. `get_hearing_questions` ツールでヒアリング質問を取得してください。\n"
            "4. `get_hearing_flow` ツールでヒアリングフローを取得してください。\n"
            "5. フローに従って質問を提示し、利用者の回答を `save_answer` で保存してください。\n"
            "6. 全ての必要な質問に回答が得られたら、`complete_hearing` でヒアリングを完了してください。\n\n"
        )

    def _design_phase() -> str:
        return (
            "## Phase 2: アーキテクチャ設計\n\n"
            "1. `get_hearing_result` ツールでヒアリング結果を取得してください。\n"
            "2. `galley://design/services` リソースから利用可能なOCIサービス一覧を確認してください。\n"
            "3. ヒアリング結果の要件に基づいて、最適なOCIサービスの組み合わせを検討してください。\n"
            "4. `save_architecture` ツールでアーキテクチャを保存してください。\n"
            "5. `validate_architecture` ツールでバリデーションを実行してください。\n"
            "6. 問題があれば `configure_component` で設定を修正してください。\n\n"
        )

    def _terraform_phase() -> str:
        return (
            "## Phase 3: IaCコード生成\n\n"
            "1. `export_iac` ツールでTerraformテンプレートを取得してください。\n"
            "2. テンプレートを元に、要件に合わせたTerraformコードを作成・配置してください。\n\n"
            "## Phase 4: Terraform実行\n\n"
            "1. `run_terraform_plan` ツールでplanを実行してください。\n"
            "2. planがエラーを返した場合、`stderr` を分析してコードを修正し、再度planを実行してください。\n"
            "3. planが成功したら、`plan_summary` で変更内容を確認してから "
            "`run_terraform_apply` でapplyを実行してください。\n\n"
        )

    def _app_phase() -> str:
        return (
            "## Phase 5: テンプレート選択\n\n"
            "1. `list_templates` ツールで利用可能なテンプレート一覧を取得してください。\n"
            "2. ヒアリング結果とアーキテクチャに最適なテンプレートを選択してください。\n"
            "3. `scaffold_from_template` ツールでプロジェクトを生成してください。\n\n"
            "## Phase 6: アプリケーションカスタマイズ\n\n"
            "1. 生成されたプロジェクトのファイル構成を確認してください。\n"
            "2. 顧客要件に合わせて `update_app_code` ツールでコードを修正してください。\n\n"
            "## Phase 7: デプロイ\n\n"
            "1. `build_and_deploy` ツールでビルド・デプロイを実行してください。\n"
            "2. `check_app_status` ツールでデプロイ状態を確認してください。\n\n"
        )

    def _notes() -> str:
        return (
            "## 注意事項\n\n"
            "- **セッションIDは利用者が後続の操作で参照できるよう、必ず明示的に伝えてください。**\n"
            "- 必須質問（required: true）は必ず回答を得てください。\n"
            "- 利用者の回答があいまいな場合は、追加質問で詳細を確認してください。\n"
            "- **ヒアリングは必ずチャット内の対話で行ってください。HTMLフォームやWebページを生成してはいけません。**\n"
            "- バリデーション結果のerrorは必ず対応してください。warningは推奨事項です。\n"
            "- 同一セッションで複数のTerraform操作を同時に実行することはできません。\n"
        )

    @mcp.prompt()
    async def build_infrastructure() -> str:
        """インフラのみを構築するエンドツーエンドワークフロー。

        ヒアリング→設計→Terraform plan→applyまでのフローをガイドします。
        """
        return (
            "# OCIインフラストラクチャ構築ワークフロー\n\n"
            "OCIインフラストラクチャをヒアリングからTerraform applyまで構築します。\n\n"
            + _hearing_phase()
            + _design_phase()
            + _terraform_phase()
            + _notes()
        )

    @mcp.prompt()
    async def build_full_stack() -> str:
        """インフラ＋アプリケーションをフルスタックで構築するエンドツーエンドワークフロー。

        ヒアリング→設計→Terraform→テンプレート選択→カスタマイズ→デプロイまでの
        フローをガイドします。
        """
        return (
            "# OCIフルスタック構築ワークフロー\n\n"
            "OCIインフラストラクチャからアプリケーションデプロイまでフルスタックで構築します。\n\n"
            + _hearing_phase()
            + _design_phase()
            + _terraform_phase()
            + _app_phase()
            + _notes()
        )
