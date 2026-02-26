"""アーキテクチャバリデーションロジック。"""

import re
from pathlib import Path
from typing import Any

import yaml

from galley.models.architecture import Architecture, Component
from galley.models.validation import ValidationResult, ValidationRule

# OCI APIリソース名にスペースを許容しないサービスタイプ
_NAME_STRICT_SERVICES: set[str] = {"nosql", "objectstorage", "streaming"}


class ArchitectureValidator:
    """バリデーションルールに基づくアーキテクチャ検証を行う。"""

    def __init__(self, config_dir: Path) -> None:
        self._config_dir = config_dir
        self._rules: list[ValidationRule] | None = None

    def _load_rules(self) -> list[ValidationRule]:
        """バリデーションルールをYAMLファイルから読み込む。"""
        if self._rules is not None:
            return self._rules

        rules: list[ValidationRule] = []
        rules_dir = self._config_dir / "validation-rules"
        if not rules_dir.exists():
            self._rules = rules
            return rules

        for rule_file in sorted(rules_dir.glob("*.yaml")):
            with open(rule_file, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if data and "rules" in data:
                for rule_data in data["rules"]:
                    rules.append(ValidationRule.model_validate(rule_data))

        self._rules = rules
        return rules

    def validate(self, architecture: Architecture) -> list[ValidationResult]:
        """アーキテクチャ構成をバリデーションルールに基づいて検証する。

        Args:
            architecture: 検証対象のアーキテクチャ。

        Returns:
            検出された問題のリスト。問題がない場合は空リスト。
        """
        rules = self._load_rules()
        results: list[ValidationResult] = []

        component_map = {c.id: c for c in architecture.components}

        for rule in rules:
            rule_results = self._apply_rule(rule, architecture, component_map)
            results.extend(rule_results)

        # コンポーネント単体のバリデーション（コードベースのルール）
        results.extend(self._check_naming_rules(architecture))
        results.extend(self._check_subnet_placement(architecture))

        return results

    def _apply_rule(
        self,
        rule: ValidationRule,
        architecture: Architecture,
        component_map: dict[str, Any],
    ) -> list[ValidationResult]:
        """単一のバリデーションルールを適用する。"""
        results: list[ValidationResult] = []
        source_service = rule.condition.get("source_service")
        target_service = rule.condition.get("target_service")

        if source_service is None or target_service is None:
            return results

        # 接続ベースのルール: 該当するConnectionを検索
        for connection in architecture.connections:
            source = component_map.get(connection.source_id)
            target = component_map.get(connection.target_id)
            if source is None or target is None:
                continue

            if source.service_type != source_service or target.service_type != target_service:
                continue

            # ルールの要件チェック
            violation = self._check_requirement(rule, target)
            if violation:
                results.append(
                    ValidationResult(
                        severity=rule.severity,
                        rule_id=rule.id,
                        message=rule.description,
                        affected_components=[connection.source_id, connection.target_id],
                        recommendation=rule.recommendation,
                    )
                )

        return results

    def _check_requirement(self, rule: ValidationRule, target: Any) -> bool:
        """ルールの要件が満たされていないかチェックする。

        Returns:
            True: 違反がある（要件が満たされていない）
            False: 問題なし（要件が満たされている）
        """
        requirement = rule.requirement

        # target_config チェック: ターゲットコンポーネントの設定値を検証
        target_config_req = requirement.get("target_config")
        if target_config_req is not None:
            for key, expected_value in target_config_req.items():
                actual_value = target.config.get(key)
                if actual_value != expected_value:
                    return True

        return False

    @staticmethod
    def _check_naming_rules(architecture: Architecture) -> list[ValidationResult]:
        """コンポーネント名のOCI命名規則チェック。

        スペースを含む名前のnosql/objectstorage/streamingコンポーネントを検出する。
        """
        results: list[ValidationResult] = []
        for comp in architecture.components:
            if comp.service_type in _NAME_STRICT_SERVICES and (
                " " in comp.display_name or not re.match(r"^[a-zA-Z0-9_-]+$", comp.display_name)
            ):
                results.append(
                    ValidationResult(
                        severity="warning",
                        rule_id="naming-convention",
                        message=(
                            f"{comp.display_name} ({comp.service_type}): "
                            "OCI APIリソース名に使用できない文字が含まれています"
                        ),
                        affected_components=[comp.id],
                        recommendation=(
                            "display_nameには英数字、アンダースコア、ハイフンのみを使用してください。"
                            "IaC生成時にはサニタイズされますが、意図した名前と異なる可能性があります。"
                        ),
                    )
                )
        return results

    @staticmethod
    def _check_subnet_placement(architecture: Architecture) -> list[ValidationResult]:
        """publicリソースのサブネット配置整合性チェック。

        deployed_in接続を持つpublicリソースがprivateサブネットに配置されていないか検出する。
        """
        results: list[ValidationResult] = []
        component_map: dict[str, Component] = {c.id: c for c in architecture.components}

        # publicリソースの判定ルール
        _PUBLIC_SERVICES: dict[str, dict[str, str]] = {
            "loadbalancer": {"config_key": "is_private", "private_value": "true"},
            "apigateway": {"config_key": "endpoint_type", "private_value": "private"},
        }

        for conn in architecture.connections:
            if conn.connection_type != "deployed_in":
                continue

            source = component_map.get(conn.source_id)
            target = component_map.get(conn.target_id)
            if source is None or target is None:
                continue

            # source が publicリソースで、target が private subnet の場合
            if target.service_type != "subnet":
                continue

            is_private_subnet = str(target.config.get("prohibit_public_ip", "false")).lower() == "true"
            if not is_private_subnet:
                continue

            rule = _PUBLIC_SERVICES.get(source.service_type)
            if rule is None:
                continue

            config_val = str(source.config.get(rule["config_key"], "")).lower()
            is_private_resource = config_val == rule["private_value"]
            if not is_private_resource:
                results.append(
                    ValidationResult(
                        severity="error",
                        rule_id="public-resource-private-subnet",
                        message=(
                            f"{source.display_name} ({source.service_type}): "
                            f"パブリックリソースがプライベートサブネット({target.display_name})に配置されています"
                        ),
                        affected_components=[conn.source_id, conn.target_id],
                        recommendation=(
                            "パブリックリソース（Public LB, Public API Gateway等）は"
                            "パブリックサブネットに配置してください"
                        ),
                    )
                )

        return results
