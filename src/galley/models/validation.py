"""バリデーション関連のデータモデル。"""

from typing import Any

from pydantic import BaseModel


class ValidationResult(BaseModel):
    """アーキテクチャバリデーションの個別検証結果。"""

    severity: str
    rule_id: str
    message: str
    affected_components: list[str]
    recommendation: str


class ValidationRule(BaseModel):
    """バリデーションルール定義（YAMLから読み込み）。"""

    id: str
    description: str
    severity: str
    condition: dict[str, Any]
    requirement: dict[str, Any]
    recommendation: str
