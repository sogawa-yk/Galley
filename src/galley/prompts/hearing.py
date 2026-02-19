"""ヒアリング関連のMCPプロンプト定義。"""

from fastmcp import FastMCP


def register_hearing_prompts(mcp: FastMCP) -> None:
    """ヒアリング関連のMCPプロンプトを登録する。"""

    @mcp.prompt()
    async def start_hearing() -> str:
        """新しいヒアリングセッションを開始するためのプロンプト。

        セッション作成から質問の提示、回答の保存、ヒアリング完了までの
        フローをガイドします。
        """
        return (
            "OCIソリューション構築のためのヒアリングを開始します。\n\n"
            "## 手順\n\n"
            "1. `create_session` ツールでセッションを作成してください。\n"
            "2. **作成されたセッションID（`session_id`）を利用者に必ず提示してください。**"
            " セッションIDは以降の全ての操作で必要です。\n"
            "3. `get_hearing_questions` ツールでヒアリング質問を取得してください。\n"
            "4. `get_hearing_flow` ツールでヒアリングフローを取得してください。\n"
            "5. フローに従って質問を提示し、利用者の回答を `save_answer` で保存してください。\n"
            "6. 全ての必要な質問に回答が得られたら、`complete_hearing` でヒアリングを完了してください。\n\n"
            "## 注意事項\n\n"
            "- **セッションIDは利用者が後続の操作で参照できるよう、必ず明示的に伝えてください。**\n"
            "- 必須質問（required: true）は必ず回答を得てください。\n"
            "- 利用者の回答があいまいな場合は、追加質問で詳細を確認してください。\n"
            "- 回答は `save_answer` または `save_answers_batch` で保存します。\n"
            "- **ヒアリングは必ずチャット内の対話で行ってください。HTMLフォームやWebページを生成してはいけません。**\n"
        )

    @mcp.prompt()
    async def resume_hearing(session_id: str) -> str:
        """既存のヒアリングセッションを再開するためのプロンプト。

        Args:
            session_id: 再開するセッションのID。
        """
        return (
            f"ヒアリングセッション `{session_id}` を再開します。\n\n"
            "## 手順\n\n"
            "1. `get_hearing_questions` ツールでヒアリング質問を取得してください。\n"
            "2. まだ回答されていない質問を特定してください。\n"
            "3. 未回答の質問を利用者に提示し、回答を `save_answer` で保存してください。\n"
            "4. 全ての必要な質問に回答が得られたら、`complete_hearing` でヒアリングを完了してください。\n\n"
            "## 注意事項\n\n"
            "- **ヒアリングは必ずチャット内の対話で行ってください。HTMLフォームやWebページを生成してはいけません。**\n"
        )
