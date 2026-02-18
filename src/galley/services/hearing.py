"""ヒアリングセッションの管理とフロー制御を行うサービス。"""

import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from galley.models.errors import (
    HearingAlreadyCompletedError,
    HearingNotCompletedError,
    StorageError,
)
from galley.models.session import Answer, HearingResult, Requirement, Session
from galley.storage.service import StorageService


class HearingService:
    """ヒアリングセッションの管理とフロー制御を行う。"""

    def __init__(self, storage: StorageService, config_dir: Path) -> None:
        self._storage = storage
        self._config_dir = config_dir
        self._questions: list[dict[str, Any]] | None = None

    def _load_questions(self) -> list[dict[str, Any]]:
        """ヒアリング質問定義を読み込む。"""
        if self._questions is None:
            questions_file = self._config_dir / "hearing-questions.yaml"
            try:
                with open(questions_file, encoding="utf-8") as f:
                    data = yaml.safe_load(f)
            except FileNotFoundError:
                raise StorageError(f"質問定義ファイルが見つかりません: {questions_file}") from None
            self._questions = data["questions"]
        return self._questions

    async def create_session(self) -> Session:
        """新しいヒアリングセッションを作成する。

        Returns:
            作成されたセッション。
        """
        session = Session(id=str(uuid.uuid4()))
        await self._storage.save_session(session)
        return session

    async def save_answer(
        self,
        session_id: str,
        question_id: str,
        value: str | list[str],
    ) -> Answer:
        """ヒアリング回答を保存する。

        Args:
            session_id: セッションID。
            question_id: 質問ID。
            value: 回答値。

        Returns:
            保存された回答。

        Raises:
            SessionNotFoundError: セッションが存在しない場合。
            HearingAlreadyCompletedError: ヒアリングが既に完了している場合。
        """
        session = await self._storage.load_session(session_id)
        if session.status == "completed":
            raise HearingAlreadyCompletedError(session_id)

        answer = Answer(question_id=question_id, value=value)
        session.answers[question_id] = answer
        session.updated_at = datetime.now(UTC)
        await self._storage.save_session(session)
        return answer

    async def save_answers_batch(
        self,
        session_id: str,
        answers: list[dict[str, Any]],
    ) -> list[Answer]:
        """複数のヒアリング回答を一括保存する。

        Args:
            session_id: セッションID。
            answers: 回答リスト。各要素は {"question_id": str, "value": str | list[str]}。

        Returns:
            保存された回答のリスト。

        Raises:
            SessionNotFoundError: セッションが存在しない場合。
            HearingAlreadyCompletedError: ヒアリングが既に完了している場合。
        """
        session = await self._storage.load_session(session_id)
        if session.status == "completed":
            raise HearingAlreadyCompletedError(session_id)

        saved_answers: list[Answer] = []
        for answer_data in answers:
            answer = Answer(
                question_id=answer_data["question_id"],
                value=answer_data["value"],
            )
            session.answers[answer_data["question_id"]] = answer
            saved_answers.append(answer)

        session.updated_at = datetime.now(UTC)
        await self._storage.save_session(session)
        return saved_answers

    async def complete_hearing(self, session_id: str) -> HearingResult:
        """ヒアリングを完了し、構造化された結果を生成する。

        Args:
            session_id: セッションID。

        Returns:
            構造化されたヒアリング結果。

        Raises:
            SessionNotFoundError: セッションが存在しない場合。
            HearingAlreadyCompletedError: ヒアリングが既に完了している場合。
        """
        session = await self._storage.load_session(session_id)
        if session.status == "completed":
            raise HearingAlreadyCompletedError(session_id)

        hearing_result = self._build_hearing_result(session)
        session.hearing_result = hearing_result
        session.status = "completed"
        session.updated_at = datetime.now(UTC)
        await self._storage.save_session(session)
        return hearing_result

    async def get_hearing_result(self, session_id: str) -> HearingResult:
        """ヒアリング結果を取得する。

        Args:
            session_id: セッションID。

        Returns:
            ヒアリング結果。

        Raises:
            SessionNotFoundError: セッションが存在しない場合。
            HearingNotCompletedError: ヒアリングが未完了の場合。
        """
        session = await self._storage.load_session(session_id)
        if session.hearing_result is None:
            raise HearingNotCompletedError(session_id)
        return session.hearing_result

    def _build_hearing_result(self, session: Session) -> HearingResult:
        """回答から構造化されたヒアリング結果を生成する。"""
        questions = self._load_questions()
        question_map = {q["id"]: q for q in questions}

        requirements: list[Requirement] = []
        constraints: list[str] = []
        summary_parts: list[str] = []

        for question_id, answer in session.answers.items():
            question = question_map.get(question_id)
            if question is None:
                continue

            category = question.get("category", "other")
            value = answer.value if isinstance(answer.value, str) else ", ".join(answer.value)

            summary_parts.append(f"- **{question['text']}**: {value}")

            if category in ("compute", "database", "network", "security"):
                is_required = question.get("required", False)
                requirements.append(
                    Requirement(
                        category=category,
                        description=f"{question['text']}: {value}",
                        priority="must" if is_required else "should",
                    )
                )
            elif category == "other" and value.strip():
                constraints.append(f"{question['text']}: {value}")

        summary = "# ヒアリング結果サマリー\n\n" + "\n".join(summary_parts)

        return HearingResult(
            session_id=session.id,
            summary=summary,
            requirements=requirements,
            constraints=constraints,
        )
