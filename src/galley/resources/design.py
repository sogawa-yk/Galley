"""設計関連のMCPリソース定義。"""

from pathlib import Path

import yaml
from fastmcp import FastMCP


def register_design_resources(mcp: FastMCP, config_dir: Path) -> None:
    """設計関連のMCPリソースを登録する。"""

    @mcp.resource("galley://design/services")
    async def oci_services() -> str:
        """利用可能なOCIサービス定義を取得する。

        アーキテクチャに追加可能なOCIサービスの一覧を返します。
        各サービスにはサービス種別、表示名、説明、設定スキーマが含まれます。
        """
        services_file = config_dir / "oci-services.yaml"
        with open(services_file, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return yaml.dump(data, allow_unicode=True, default_flow_style=False)

    @mcp.resource("galley://design/validation-rules")
    async def validation_rules() -> str:
        """バリデーションルール定義を取得する。

        アーキテクチャ検証に使用されるバリデーションルールの一覧を返します。
        """
        rules_dir = config_dir / "validation-rules"
        all_rules: dict[str, list[dict]] = {"rules": []}  # type: ignore[type-arg]
        if rules_dir.exists():
            for rule_file in sorted(rules_dir.glob("*.yaml")):
                with open(rule_file, encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                if data and "rules" in data:
                    all_rules["rules"].extend(data["rules"])
        return yaml.dump(all_rules, allow_unicode=True, default_flow_style=False)
