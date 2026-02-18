"""アーキテクチャ関連のデータモデル。"""

import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class Component(BaseModel):
    """アーキテクチャを構成するOCIサービスコンポーネント。"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    service_type: str
    display_name: str
    config: dict[str, Any] = Field(default_factory=dict)
    customizable: bool = True


class Connection(BaseModel):
    """コンポーネント間の接続関係。"""

    source_id: str
    target_id: str
    connection_type: str
    description: str


class Architecture(BaseModel):
    """OCIアーキテクチャ定義。"""

    session_id: str
    components: list[Component] = Field(default_factory=list)
    connections: list[Connection] = Field(default_factory=list)
    validation_results: list[Any] | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
