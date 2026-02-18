"""設計支援のMCPプロンプト定義。"""

from fastmcp import FastMCP


def register_design_prompts(mcp: FastMCP) -> None:
    """設計関連のMCPプロンプトを登録する。"""

    @mcp.prompt()
    async def auto_design(session_id: str) -> str:
        """自動設計モードを開始するためのプロンプト。

        ヒアリング結果を分析し、推奨アーキテクチャを自動生成するフローをガイドします。

        Args:
            session_id: セッションID。
        """
        return (
            f"セッション `{session_id}` のヒアリング結果から推奨アーキテクチャを生成します。\n\n"
            "## 手順\n\n"
            "1. `get_hearing_result` ツールでヒアリング結果を取得してください。\n"
            "2. `galley://design/services` リソースから利用可能なOCIサービス一覧を確認してください。\n"
            "3. ヒアリング結果の要件に基づいて、最適なOCIサービスの組み合わせを検討してください。\n"
            "4. `save_architecture` ツールでアーキテクチャを保存してください。\n"
            "5. `validate_architecture` ツールでバリデーションを実行してください。\n"
            "6. 問題があれば `configure_component` で設定を修正してください。\n\n"
            "## 注意事項\n\n"
            "- 各コンポーネントにはservice_type、display_name、configを指定してください。\n"
            "- コンポーネント間の接続関係も忘れずに定義してください。\n"
            "- バリデーション結果のerrorは必ず対応してください。warningは推奨事項です。\n"
        )

    @mcp.prompt()
    async def interactive_design(session_id: str) -> str:
        """対話型設計モードを開始するためのプロンプト。

        利用者がアーキテクチャを対話的に組み立てるフローをガイドします。

        Args:
            session_id: セッションID。
        """
        return (
            f"セッション `{session_id}` のアーキテクチャを対話的に設計します。\n\n"
            "## 手順\n\n"
            "1. `list_available_services` ツールで利用可能なOCIサービスを確認してください。\n"
            "2. 利用者と対話しながら、`add_component` でコンポーネントを追加してください。\n"
            "3. 必要に応じて `configure_component` で設定を調整してください。\n"
            "4. 不要なコンポーネントは `remove_component` で削除できます。\n"
            "5. 構成が完成したら `validate_architecture` でバリデーションを実行してください。\n"
            "6. 問題がなければ `export_all` で成果物をエクスポートしてください。\n\n"
            "## 注意事項\n\n"
            "- `galley://design/services` リソースで各サービスの設定スキーマを確認できます。\n"
            "- `galley://design/validation-rules` リソースでバリデーションルールを確認できます。\n"
            "- 利用者の設計判断を尊重しつつ、バリデーション結果に基づいたフィードバックを提供してください。\n"
        )
