"""Galleyサーバーの設定管理。"""

from pathlib import Path

from pydantic_settings import BaseSettings

_PACKAGE_ROOT = Path(__file__).parent
_REPO_ROOT = _PACKAGE_ROOT.parent.parent


class ServerConfig(BaseSettings):
    """サーバー設定。環境変数から読み込み可能。"""

    model_config = {"env_prefix": "GALLEY_"}

    data_dir: Path = _REPO_ROOT / ".galley"
    config_dir: Path = _REPO_ROOT / "config"
    host: str = "0.0.0.0"
    port: int = 8000
    url_token: str = ""

    # Object Storage (Terraform自動設定)
    bucket_name: str = ""
    bucket_namespace: str = ""
    region: str = ""

    # Build Instance (Terraform自動設定)
    build_instance_id: str = ""

    # OCIR認証 (Terraform自動設定)
    ocir_endpoint: str = ""
    ocir_username: str = ""
    ocir_auth_token: str = ""
