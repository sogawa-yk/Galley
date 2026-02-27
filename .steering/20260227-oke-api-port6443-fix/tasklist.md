# タスクリスト

## タスク完全完了の原則

**このファイルの全タスクが完了するまで作業を継続すること**

---

## フェーズ1: OKE追加ルールのPublic/Private分離

- [x] `_expand_vcn_network` の `oke_extra_rules` を `oke_public_extra_rules` と `oke_private_extra_rules` に分離
- [x] `oke_public_extra_rules` にTCP 6443 from 0.0.0.0/0ルールを追加
- [x] Public SLのconfigに `oke_public_extra_rules` を使用
- [x] Private SLのconfigに `oke_private_extra_rules` を使用

## フェーズ2: テスト追加

- [x] OKE構成でPublic SLにport 6443ルールが含まれることをテスト
- [x] OKE構成でPrivate SLにport 6443ルールが含まれないことをテスト

---

## 実装後の振り返り

### 実装完了日
2026-02-27

### 計画と実績の差分

**計画と異なった点**:
- なし。計画通りに実装完了。

**新たに必要になったタスク**:
- Ruffフォーマット修正: `_oke_common_rules + "\n..."` の演算子位置がBlack互換スタイルに違反。implementation-validatorが検出・修正。

### 学んだこと

**技術的な学び**:
- OKE Security Listのルールは用途（Public SL: 外部アクセス、Private SL: ノード間通信）に応じて分離すべき。一律に同じルールを注入するのは不適切。
- `_oke_common_rules` 中間変数でPublic/Private共通部分を抽出し、Public SL固有のport 6443ルールを追加する文字列連結パターンが既存の `{sgw_route_block}` パターンと一貫。

### 次回への改善提案
- OKEの `endpoint_config.is_public_ip_enabled` がfalseの場合（Private Endpoint）、port 6443はPublic SLではなくPrivate SLに必要になる。現状はPublic Endpoint固定なので問題ないが、将来Private Endpoint対応時に再検討が必要。
