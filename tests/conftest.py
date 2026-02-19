"""テスト共通フィクスチャ。"""

from pathlib import Path

import pytest

from galley.config import ServerConfig
from galley.services.design import DesignService
from galley.services.hearing import HearingService
from galley.services.infra import InfraService
from galley.storage.service import StorageService


@pytest.fixture
def tmp_data_dir(tmp_path: Path) -> Path:
    """テスト用の一時データディレクトリ。"""
    return tmp_path / "galley-test"


@pytest.fixture
def config_dir() -> Path:
    """設定ファイルディレクトリ。"""
    return Path(__file__).parent.parent / "config"


@pytest.fixture
def storage(tmp_data_dir: Path) -> StorageService:
    """テスト用StorageService。"""
    return StorageService(data_dir=tmp_data_dir)


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


@pytest.fixture
def server_config(tmp_data_dir: Path, config_dir: Path) -> ServerConfig:
    """テスト用ServerConfig。"""
    return ServerConfig(data_dir=tmp_data_dir, config_dir=config_dir)
