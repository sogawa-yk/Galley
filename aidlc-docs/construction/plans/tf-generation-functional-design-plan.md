# Functional Design Plan - Unit 2: Terraform Generation

## Plan Steps

- [x] ビジネスロジックモデル設計（business-logic-model.md）
- [x] ビジネスルール設計（business-rules.md）
- [x] ドメインエンティティ設計（domain-entities.md）
- [x] 設計の整合性検証

---

## Design Questions

## Question 1

Terraformコードの生成方式はどうしますか？

A) テンプレートベース — OCIリソースタイプごとにTerraformテンプレート(.tf.tmpl)を事前用意し、パラメータを埋め込む
B) 完全動的生成 — Claude CodeがTerraformコードをゼロから生成する（テンプレートなし）
C) モジュール参照型 — OCI公式Terraformモジュール（terraform-oci-\*）を参照するコードを生成する
D) Other (please describe after [Answer]: tag below)

[Answer]: C（対応できないものはB）

## Question 2

Terraform stateの管理方法はどうしますか？（Resource Managerを使う前提）

A) Resource Managerに完全委任（state管理不要、RM Stackが管理）
B) OCI Object Storageにremote stateを設定
C) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 3

生成するTerraformコードのファイル分割粒度はどうしますか？

A) リソースタイプ別ファイル（network.tf, compute.tf, database.tf, etc.）
B) 単一ファイル（main.tf に全リソース）
C) モジュール構成（modules/network/, modules/compute/, etc.）
D) Other (please describe after [Answer]: tag below)

[Answer]: A
