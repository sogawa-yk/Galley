"""アプリケーション層関連のデータモデル。"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class TemplateParameter(BaseModel):
    """テンプレートのカスタマイズ可能なパラメータ。"""

    name: str
    description: str
    param_type: Literal["string", "number", "boolean", "choice"]
    required: bool = True
    default: Any | None = None
    choices: list[str] | None = None


class TemplateMetadata(BaseModel):
    """テンプレートのメタデータ。"""

    name: str
    display_name: str
    description: str
    parameters: list[TemplateParameter] = Field(default_factory=list)
    protected_paths: list[str] = Field(default_factory=list)


class DeployResult(BaseModel):
    """ビルド・デプロイの実行結果。"""

    success: bool
    image_uri: str | None = None
    endpoint: str | None = None
    rolled_back: bool = False
    reason: str | None = None


class AppStatus(BaseModel):
    """アプリケーションのデプロイ状態。"""

    session_id: str
    status: Literal["not_deployed", "deploying", "running", "failed"] = "not_deployed"
    endpoint: str | None = None
    health_check: dict[str, Any] | None = None
    last_deployed_at: datetime | None = None
