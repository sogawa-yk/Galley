"""アーキテクチャバリデーションロジック。"""

from pathlib import Path
from typing import Any

import yaml

from galley.models.architecture import Architecture
from galley.models.validation import ValidationResult, ValidationRule


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
