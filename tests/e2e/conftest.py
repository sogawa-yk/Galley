"""E2Eテスト専用フィクスチャ。"""

from pathlib import Path
from typing import Any

import pytest

from galley.services.design import DesignService
from galley.services.hearing import HearingService
from galley.services.infra import InfraService
from galley.storage.service import StorageService

# デフォルト値（docs/environment.md参照）
_DEFAULT_COMPARTMENT_ID = "ocid1.compartment.oc1..aaaaaaaanxm4oucgt5pkgd7sw2vouvckvvxan7ca2lirowaao7krnzlkdkhq"
_DEFAULT_REGION = "ap-osaka-1"


@pytest.fixture
def oci_compartment_id() -> str:
    """OCI compartment ID（環境変数 or デフォルト）。"""
    import os

    return os.environ.get("GALLEY_TEST_COMPARTMENT_ID", _DEFAULT_COMPARTMENT_ID)


@pytest.fixture
def oci_region() -> str:
    """OCI region（環境変数 or デフォルト）。"""
    import os

    return os.environ.get("GALLEY_TEST_REGION", _DEFAULT_REGION)


@pytest.fixture
def terraform_variables(oci_compartment_id: str, oci_region: str) -> dict[str, str]:
    """Terraform用の変数辞書。"""
    return {
        "compartment_id": oci_compartment_id,
        "region": oci_region,
    }


@pytest.fixture
def config_dir() -> Path:
    """設定ファイルディレクトリ。"""
    return Path(__file__).parent.parent.parent / "config"


@pytest.fixture
def storage(tmp_path: Path) -> StorageService:
    """テスト用StorageService。"""
    return StorageService(data_dir=tmp_path / "galley-e2e")


@pytest.fixture
def hearing_service(storage: StorageService, config_dir: Path) -> HearingService:
    """テスト用HearingService。"""
    return HearingService(storage=storage, config_dir=config_dir)


@pytest.fixture
def design_service(storage: StorageService, config_dir: Path) -> DesignService:
    """テスト用DesignService。"""
    return DesignService(storage=storage, config_dir=config_dir)


@pytest.fixture
def infra_service(storage: StorageService, config_dir: Path) -> InfraService:
    """テスト用InfraService。"""
    return InfraService(storage=storage, config_dir=config_dir)


async def create_session_with_component(
    hearing_service: HearingService,
    design_service: DesignService,
    components: list[dict[str, Any]],
    connections: list[dict[str, Any]] | None = None,
) -> tuple[str, str]:
    """ヒアリング完了→アーキテクチャ保存→IaCエクスポートを一括実行する。

    Returns:
        (session_id, terraform_dir) のタプル。
    """
    session = await hearing_service.create_session()
    await hearing_service.save_answer(session.id, "purpose", "E2Eテスト")
    await hearing_service.complete_hearing(session.id)

    await design_service.save_architecture(
        session.id,
        components=components,
        connections=connections or [],
    )

    iac_result = await design_service.export_iac(session.id)
    return session.id, iac_result["terraform_dir"]
