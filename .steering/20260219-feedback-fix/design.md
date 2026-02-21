# 設計: フィードバック修正

## 変更対象ファイル

| ファイル | 変更種別 | 対応するR# |
|---------|---------|-----------|
| `src/galley/models/errors.py` | 修正 | R1 |
| `src/galley/tools/hearing.py` | 修正 | R1 |
| `src/galley/services/design.py` | 修正 | R2, R3, R4 |
| `src/galley/tools/export.py` | 修正 | R4 |
| `src/galley/services/infra.py` | 修正 | R5, R6 |
| `src/galley/tools/infra.py` | 修正 | R6 |
| `tests/unit/services/test_design.py` | 修正 | R2, R3, R4 |
| `tests/unit/services/test_infra.py` | 修正 | R5, R6 |

## 設計詳細

### D1: エラーメッセージ改善 (R1)

**`ArchitectureNotFoundError`**:
```python
def __init__(self, session_id: str) -> None:
    super().__init__(
        f"Architecture not found for session: {session_id}. "
        "Please call save_architecture first to create an architecture from the hearing results."
    )
```

**`complete_hearing`レスポンス**:
```python
return {
    ...,
    "next_step": "Use save_architecture to design the architecture based on the hearing results.",
}
```

### D2: Connection ID解決 (R2)

`save_architecture`メソッド内で:
1. componentsをパースし、仮IDとUUIDのマッピングを作成
2. connectionsのsource_id/target_idを実際のUUIDに置換

```python
# 仮ID → UUID のマッピング構築
id_mapping: dict[str, str] = {}
for i, comp_data in enumerate(components):
    original_id = comp_data.get("id", "")
    parsed = Component.model_validate(comp_data)
    # 元のIDがUUID形式でなければ新規生成
    id_mapping[original_id] = parsed.id
```

コンポーネントのIDが呼び出し元から渡された場合、それを新しいUUIDに置換し、connectionsのsource_id/target_idも同じマッピングで変換する。

### D3: Terraform テンプレート改善 (R3)

`export_iac`メソッドの`components.tf`生成を改善:

1. `config/oci-services.yaml`からサービスタイプ→Terraformリソース名のマッピングを定義
2. 各サービスタイプに対応する基本的なリソース定義テンプレートを用意
3. `repr()`ではなくJSON形式のダブルクォートで値を出力

サービスタイプ→Terraformリソースのマッピング例:
```python
_SERVICE_TO_TF_RESOURCE: dict[str, list[dict]] = {
    "vcn": [{"resource": "oci_core_vcn", "template": "..."}],
    "compute": [{"resource": "oci_core_instance", "template": "..."}],
    "oke": [{"resource": "oci_containerengine_cluster", "template": "..."}],
    "adb": [{"resource": "oci_database_autonomous_database", "template": "..."}],
    "apigateway": [{"resource": "oci_apigateway_gateway", "template": "..."}],
    "functions": [
        {"resource": "oci_functions_application", "template": "..."},
        {"resource": "oci_functions_function", "template": "..."},
    ],
    "objectstorage": [{"resource": "oci_objectstorage_bucket", "template": "..."}],
    "loadbalancer": [{"resource": "oci_load_balancer_load_balancer", "template": "..."}],
}
```

### D4: サーバー側ファイル書き出し (R4)

`export_iac`メソッドに追加:
1. セッションのデータディレクトリにterraformサブディレクトリを作成
2. 生成したファイルを書き出す
3. 書き出し先パスをレスポンスに含める

StorageServiceにセッションのデータディレクトリパスを取得するメソッドを追加（既存の`_session_dir`を公開）。

`export_iac`のレスポンスに`terraform_dir`を追加:
```python
return {
    "terraform_files": files,
    "terraform_dir": str(terraform_dir),
}
```

### D5: 自動terraform init (R5)

`_ensure_terraform_init`メソッドを追加:
```python
async def _ensure_terraform_init(self, terraform_dir: Path) -> TerraformResult | None:
    if (terraform_dir / ".terraform").exists():
        return None  # 既にinit済み
    exit_code, stdout, stderr = await self._run_subprocess(
        ["terraform", "init", "-no-color", "-input=false"],
        cwd=str(terraform_dir),
    )
    if exit_code != 0:
        return TerraformResult(
            success=False, command="plan", stdout=stdout, stderr=stderr, exit_code=exit_code
        )
    return None
```

`run_terraform_plan`, `run_terraform_apply`, `run_terraform_destroy`の各メソッドのsubprocess実行前に`_ensure_terraform_init`を呼び出す。

### D6: 変数パラメータ (R6)

`run_terraform_plan`, `run_terraform_apply`, `run_terraform_destroy`に`variables: dict[str, str] | None = None`パラメータを追加。

コマンド引数構築時に`-var`オプションを付与:
```python
args = ["terraform", "plan", "-no-color", "-input=false"]
if variables:
    for key, value in variables.items():
        args.extend(["-var", f"{key}={value}"])
```

ツール層も同様にパラメータを追加。
