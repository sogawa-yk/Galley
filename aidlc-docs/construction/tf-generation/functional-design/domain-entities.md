# Domain Entities - Unit 2: Terraform Generation

## Entity: TerraformProject

生成するTerraformプロジェクト全体。

```
TerraformProject
  - project_name: str              # プロジェクト名
  - output_dir: str                # 出力ディレクトリパス
  - resources: list[OCIResource]   # 必要なOCIリソース
  - files: list[TerraformFile]     # 生成するファイル
  - modules: list[TerraformModule] # 使用するモジュール
```

## Entity: OCIResource

必要なOCIリソースの定義。

```
OCIResource
  - type: str                      # リソースタイプ (vcn, oke, compute, etc.)
  - terraform_type: str            # Terraformリソースタイプ (oci_core_vcn, etc.)
  - name: str                      # リソース名 ({project_name}-{type})
  - parameters: dict               # リソース固有のパラメータ
  - depends_on: list[str]          # 依存リソースの名前リスト
  - use_module: bool               # 公式モジュールを使用するか
  - module_source: str | None      # モジュールソース (use_module=true時)
  - file_target: str               # 出力先ファイル名 (network.tf, compute.tf, etc.)
  - tags: dict                     # freeform_tags
```

## Entity: TerraformFile

生成するTerraformファイル。

```
TerraformFile
  - filename: str                  # ファイル名 (provider.tf, network.tf, etc.)
  - content: str                   # 生成されたHCLコード
  - required: bool                 # 常に生成するか条件付きか
  - condition: str | None          # 生成条件 (required=false時)
```

## Entity: TerraformModule

使用する公式モジュールの定義。

```
TerraformModule
  - name: str                      # モジュール名
  - source: str                    # モジュールソース
  - version: str                   # バージョン制約
  - inputs: dict                   # モジュール入力変数
```

## Entity: TerraformVariable

変数定義。

```
TerraformVariable
  - name: str                      # 変数名
  - type: str                      # 型 (string, number, bool, list, map)
  - description: str               # 説明
  - default: any | None            # デフォルト値
  - required: bool                 # 必須か
```

## Entity: TerraformOutput

出力値定義。

```
TerraformOutput
  - name: str                      # 出力名
  - value: str                     # 値のHCL式
  - description: str               # 説明
  - sensitive: bool                # 機密値か
```

## Entity Relationships

```
TerraformProject 1---* OCIResource
TerraformProject 1---* TerraformFile
TerraformProject 1---* TerraformModule
TerraformFile 1---* OCIResource (contained in)
TerraformFile 1---* TerraformVariable
TerraformFile 1---* TerraformOutput
OCIResource *---0..1 TerraformModule (uses)
OCIResource *---* OCIResource (depends_on)
```
