"""ヒアリングセッション関連のデータモデル。"""

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field

from galley.models.architecture import Architecture

SessionStatus = Literal["in_progress", "completed"]


class Requirement(BaseModel):
    """構造化された要件。"""

    category: str
    description: str
    priority: Literal["must", "should", "could"]


class Answer(BaseModel):
    """ヒアリングの個別質問に対する回答。"""

    question_id: str
    value: str | list[str]
    answered_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class HearingResult(BaseModel):
    """ヒアリング完了後の構造化された要件情報。"""

    session_id: str
    summary: str
    requirements: list[Requirement]
    constraints: list[str]
    completed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Session(BaseModel):
    """ヒアリングセッション。"""

    id: str
    status: SessionStatus = "in_progress"
    answers: dict[str, Answer] = Field(default_factory=dict)
    hearing_result: HearingResult | None = None
    architecture: Architecture | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
