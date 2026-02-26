# 設計書

## アーキテクチャ概要

既存の`DesignService`（`src/galley/services/design.py`）のIaC生成ロジックを修正する。変更は主に以下のメソッド/データ構造に集中する:

```
design.py
├── _TF_RESOURCE_TEMPLATES (テンプレート修正・追加)
├── _TF_REQUIRED_VARS (変数定義追加)
├── _TF_DEFAULTS (デフォルト値修正)
├── _build_local_references() (複数サブネット/ルートテーブル/ゲートウェイ対応)
├── _expand_vcn_network() (NAT GW自動生成追加)
├── _render_component_tf() (endpoint_type大文字化、名前サニタイズ)
└── export_iac() (サブネット割り当てロジック修正)

validators/architecture.py
├── validate() (構造ベースのバリデーション追加)
└── _check_component_rules() (新規: コンポーネント単体のルールチェック)
```

## コンポーネント設計

### 1. サブネット割り当てロジック修正（`_build_local_references`）

**責務**:
- 複数サブネットがある場合に、public/privateを区別したマッピングを構築
- ルートテーブル、セキュリティリスト、ゲートウェイも同様にpublic/privateを区別

**実装の要点**:
- `_build_local_references()`の戻り値を変更: 単一のvar→ref マッピングから、コンポーネントごとの参照解決に拡張
- サブネットの`prohibit_public_ip`設定で public/private を判定
  - `prohibit_public_ip == "false"` or `false` → public
  - `prohibit_public_ip == "true"` or `true` → private
- ルートテーブル名に "private" が含まれるかでpublic/private判定
- セキュリティリスト名に "private" が含まれるかでpublic/private判定
- ゲートウェイ: IGW → public route table, NAT GW → private route table

**設計変更**:
```python
# Before: 単一マッピング（最後のコンポーネントで上書き）
refs["var.subnet_id"] = "oci_core_subnet.last_subnet.id"

# After: public/private別のマッピング
refs["var.subnet_id"] = "oci_core_subnet.public_subnet.id"  # デフォルト
refs["var.private_subnet_id"] = "oci_core_subnet.private_subnet.id"  # private用
```

ただし、既存テンプレートは全て `var.subnet_id` を使っているため、参照置換の段階でコンポーネントの特性に応じて適切なサブネットに振り分ける方が後方互換性が高い。

**採用する方式**: `export_iac()`内のローカル参照置換ループで、コンポーネントのサービスタイプやconfig（is_private等）に基づいて、public/privateサブネットを選択的に適用する。

### 2. リソース名サニタイズ（テンプレート修正）

**責務**:
- OCI APIに渡す`name`フィールドにサニタイズ済み名を使用
- `display_name`は人間可読のまま維持

**実装の要点**:
- `_render_component_tf()`で`safe_name`を`params`に追加し、テンプレートから参照可能にする
- nosql: `name = "{safe_name}"`, `ddl_statement = "CREATE TABLE {safe_name} ..."`
- objectstorage: `name = "{safe_name}"`
- streaming: `name = "{safe_name}"`

### 3. API Gateway endpoint_type大文字化

**実装の要点**:
- `_render_component_tf()`でservice_type=="apigateway"の場合に`endpoint_type`を`.upper()`
- デフォルト値は既に`"PUBLIC"`なので、ユーザー設定値のみ変換が必要

### 4. ルートテーブル・ゲートウェイ参照修正

**実装の要点**:
- `_build_local_references()`でIGWとNAT GWを区別
- route_tableテンプレートに`{gateway_ref}`プレースホルダーを導入し、public route tableにはIGW、private route tableにはNAT GWを設定
- subnetテンプレートの`var.route_table_id`と`var.security_list_id`を、public/private別に解決

**設計**: `_expand_vcn_network()`でNAT GWが不足している場合に自動生成する。`_build_local_references()`でIGW/NAT GWの参照をそれぞれ`var.igw_id`/`var.nat_gw_id`としてマッピングし、route_tableのレンダリング時に名前ベースでpublic/privateを判定してゲートウェイ参照を切り替える。

### 5. OKE Node Pool生成

**実装の要点**:
- `_TF_RESOURCE_TEMPLATES["oke"]`にNode Poolリソースブロックを追加
- `node_count`, `node_shape`, `node_ocpus`, `node_memory`パラメータ追加
- `_TF_DEFAULTS["oke"]`にデフォルト値追加

### 6. ADBプライベートエンドポイント

**実装の要点**:
- `_render_component_tf()`でendpoint_type=="private"の場合に`subnet_id`と`nsg_ids`を追加
- テンプレートを条件付きで拡張するか、private用の別テンプレートを用意

**採用する方式**: レンダリング後に条件付きでブロックを追加する。テンプレートにオプショナルブロックのプレースホルダー`{private_endpoint_block}`を追加。

### 7. バリデーション強化

**実装の要点**:
- `ArchitectureValidator.validate()`にコンポーネント単体ルールを追加
- リソース名チェック: スペースが含まれるnosql/objectstorageコンポーネントに警告
- ネットワーク整合性: publicリソース（LB, API GW等のis_private=false）がprivateサブネットに配置される場合にエラー

## データフロー

### IaC生成フロー（修正後）
```
1. export_iac() がアーキテクチャを読み込む
2. _expand_vcn_network() がNAT GW含むネットワークリソースを補完
3. _build_local_references() がpublic/private別のサブネット/RT/SL/GW参照マップを構築
4. 各コンポーネントの_render_component_tf()でサニタイズ済み名・大文字endpoint_type適用
5. ローカル参照置換でコンポーネント特性に基づくpublic/private振り分け
6. Terraformファイル出力
```

## テスト戦略

### ユニットテスト（`tests/unit/services/test_design.py`に追加）
- 複数サブネット構成でのローカル参照テスト
- NoSQL/ObjectStorage名サニタイズテスト
- API Gateway endpoint_type大文字化テスト
- OKE Node Pool生成テスト
- ADBプライベートエンドポイントテスト
- ルートテーブル・ゲートウェイ参照テスト

### バリデーションテスト
- リソース名スペース検出テスト
- publicリソースのprivateサブネット配置検出テスト

## 依存ライブラリ

新規追加なし。

## ディレクトリ構造

```
src/galley/
├── services/
│   └── design.py              # 主な修正対象
└── validators/
    └── architecture.py         # バリデーション強化

config/
└── validation-rules/
    └── connection-requirements.yaml  # （変更なし、コードベースのルール追加）

tests/unit/services/
└── test_design.py              # テスト追加
```

## 実装の順序

1. テンプレート修正（nosql/objectstorage/streaming名サニタイズ、API GW大文字化）
2. `_expand_vcn_network()`にNAT GW自動生成追加
3. `_build_local_references()`のpublic/private区別対応
4. `export_iac()`のローカル参照置換ロジック改修
5. OKE Node Poolテンプレート追加
6. ADBプライベートエンドポイント対応
7. バリデーション強化
8. テスト追加・既存テスト修正
