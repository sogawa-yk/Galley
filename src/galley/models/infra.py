"""インフラ操作関連のデータモデル。"""

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field

TerraformCommand = Literal["plan", "apply", "destroy"]


class TerraformErrorDetail(BaseModel):
    """Terraformエラーの構造化された詳細情報。"""

    file: str | None = None
    line: int | None = None
    message: str
    suggestion: str | None = None


class TerraformResult(BaseModel):
    """Terraform実行結果。"""

    success: bool
    command: TerraformCommand
    stdout: str
    stderr: str
    exit_code: int
    plan_summary: str | None = None
    errors: list[TerraformErrorDetail] | None = None


class CLIResult(BaseModel):
    """OCI CLI実行結果。"""

    success: bool
    stdout: str
    stderr: str
    exit_code: int
    setup_hint: str | None = None


RMJobStatus = Literal["ACCEPTED", "IN_PROGRESS", "SUCCEEDED", "FAILED", "CANCELING", "CANCELED"]


class RMStack(BaseModel):
    """Resource Managerスタック。"""

    id: str
    compartment_id: str
    display_name: str
    terraform_version: str
    lifecycle_state: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class RMJob(BaseModel):
    """Resource Managerジョブ。"""

    id: str
    stack_id: str
    operation: Literal["PLAN", "APPLY", "DESTROY"]
    lifecycle_state: RMJobStatus
    log_location: str | None = None
