# 設計書: インフラ層プロンプト追加

## アーキテクチャ概要

既存のプロンプト登録パターン（`prompts/hearing.py`, `prompts/design.py`）に従い、`prompts/infra.py` を追加する。

## コンポーネント設計

### prompts/infra.py

```python
def register_infra_prompts(mcp: FastMCP) -> None:
    """インフラ関連のMCPプロンプトを登録する。"""

    @mcp.prompt()
    async def terraform_debug_loop(session_id: str) -> str:
        """Terraform自動デバッグループを開始する。"""
        ...

    @mcp.prompt()
    async def oci_resource_check() -> str:
        """OCI CLIでリソース情報を確認する。"""
        ...

    @mcp.prompt()
    async def infra_cleanup(session_id: str) -> str:
        """インフラリソースをクリーンアップする。"""
        ...
```

### プロンプト内容の設計方針

- 機能設計書のUC3（Terraform自動デバッグループ）のシーケンスに沿ったガイダンス
- 具体的なツール名をステップバイステップで提示（既存パターン準拠）
- エラーハンドリング指示を含める（Terraform planのエラー時にstderrを分析して修正する旨）

## server.py への変更

```python
from galley.prompts.infra import register_infra_prompts
# ...
# インフラ層
register_infra_tools(mcp, infra_service)
register_infra_prompts(mcp)  # ← 追加
```

## テスト

- `tests/integration/test_infra_flow.py` にプロンプト登録テストを追加
  - `terraform_debug_loop`, `oci_resource_check`, `infra_cleanup` がlist_promptsに含まれることを検証
