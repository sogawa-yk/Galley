# 設計書

## アーキテクチャ概要

修正は `src/galley/services/design.py` の `_expand_vcn_network` メソッドに集中。OKE検出時の追加ルール注入ロジックをPublic/Private SL別に分離する。

## コンポーネント設計

### Public/Private SLで異なるOKE追加ルール

**現状**: `oke_extra_rules`（VCN内全TCP + ICMP）を**両方のSL**に同じ内容で注入。

**変更**: 2つの変数に分離:
- `oke_public_extra_rules`: VCN内全TCP + ICMP + **TCP 6443 from 0.0.0.0/0**
- `oke_private_extra_rules`: VCN内全TCP + ICMP（変更なし）

**理由**: port 6443はOKE API Serverへの外部アクセス用でPublic Subnetにのみ必要。Private Subnetに不要なポートを開放しない。

## テスト戦略

### ユニットテスト（追加）
- OKE構成でPublic SLにport 6443ルールが含まれることをテスト
- OKE構成でPrivate SLにport 6443ルールが含まれないことをテスト

### 既存テスト
- `test_oke_adds_additional_security_rules`: Public SLにVCN CIDR全TCP + ICMPが含まれるテスト → 変更不要（6443追加で既存ルールは保持）
- `test_no_oke_no_additional_security_rules`: OKEなし構成でICMPなし → 変更不要

## 変更ファイル

```
src/galley/services/design.py      # メイン修正
tests/unit/services/test_design.py  # テスト追加
```
