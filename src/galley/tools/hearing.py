"""ヒアリング層のMCPツール定義。"""

from typing import Any

from fastmcp import FastMCP

from galley.models.errors import GalleyError
from galley.services.hearing import HearingService


def register_hearing_tools(mcp: FastMCP, hearing_service: HearingService) -> None:
    """ヒアリング関連のMCPツールを登録する。"""

    @mcp.tool()
    async def create_session() -> dict[str, Any]:
        """新しいヒアリングセッションを作成する。

        要件ヒアリングを開始するために、まずこのツールでセッションを作成してください。
        返却されるsession_idを以降のツール呼び出しで使用します。
        """
        try:
            session = await hearing_service.create_session()
            return {"session_id": session.id, "status": session.status}
        except GalleyError as e:
            return {"error": type(e).__name__, "message": str(e)}

    @mcp.tool()
    async def save_answer(
        session_id: str,
        question_id: str,
        value: str | list[str],
    ) -> dict[str, Any]:
        """ヒアリング回答を保存する。

        Args:
            session_id: セッションID。
            question_id: 質問ID（hearing-questions.yamlで定義）。
            value: 回答値（テキストまたは複数選択のリスト）。
        """
        try:
            answer = await hearing_service.save_answer(session_id, question_id, value)
            return {
                "question_id": answer.question_id,
                "value": answer.value,
                "answered_at": answer.answered_at.isoformat(),
            }
        except GalleyError as e:
            return {"error": type(e).__name__, "message": str(e)}

    @mcp.tool()
    async def save_answers_batch(
        session_id: str,
        answers: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """複数のヒアリング回答を一括保存する。

        Args:
            session_id: セッションID。
            answers: 回答リスト。各要素は {"question_id": str, "value": str | list[str]}。
        """
        try:
            saved = await hearing_service.save_answers_batch(session_id, answers)
            return {
                "saved_count": len(saved),
                "answers": [
                    {
                        "question_id": a.question_id,
                        "value": a.value,
                        "answered_at": a.answered_at.isoformat(),
                    }
                    for a in saved
                ],
            }
        except GalleyError as e:
            return {"error": type(e).__name__, "message": str(e)}

    @mcp.tool()
    async def complete_hearing(session_id: str) -> dict[str, Any]:
        """ヒアリングを完了し、構造化された結果を生成する。

        全ての必要な質問に回答した後、このツールを呼び出してヒアリングを完了させてください。
        回答から構造化された要件情報が生成されます。

        Args:
            session_id: セッションID。
        """
        try:
            result = await hearing_service.complete_hearing(session_id)
            return {
                "session_id": result.session_id,
                "summary": result.summary,
                "requirements": [r.model_dump() for r in result.requirements],
                "constraints": result.constraints,
                "completed_at": result.completed_at.isoformat(),
            }
        except GalleyError as e:
            return {"error": type(e).__name__, "message": str(e)}

    @mcp.tool()
    async def get_hearing_result(session_id: str) -> dict[str, Any]:
        """ヒアリング結果を取得する。

        ヒアリング完了後に、構造化された要件情報を取得します。
        この結果をもとにアーキテクチャ設計を行います。

        Args:
            session_id: セッションID。
        """
        try:
            result = await hearing_service.get_hearing_result(session_id)
            return {
                "session_id": result.session_id,
                "summary": result.summary,
                "requirements": [r.model_dump() for r in result.requirements],
                "constraints": result.constraints,
                "completed_at": result.completed_at.isoformat(),
            }
        except GalleyError as e:
            return {"error": type(e).__name__, "message": str(e)}
