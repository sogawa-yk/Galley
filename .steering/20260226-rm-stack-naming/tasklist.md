# タスクリスト: RMスタック命名改善

- [x] `_build_stack_display_name()`メソッドをInfraServiceに追加
- [x] `_ensure_rm_stack()`のdisplay_name生成を新メソッドに置き換え（create/update両方）
- [x] ユニットテスト追加: display_name生成の各パターン検証
- [x] 既存テスト(`TestEnsureRmStack`)のdisplay_name検証を更新

---

## 申し送り事項

- **実装完了日**: 2026-02-26
- **計画と実績の差分**: なし。全タスク計画通り完了。
- **学んだこと**: session.answersから直接purposeを取得する方式は、hearing_result.summaryよりも確実かつ軽量。
- **次回への改善提案**: なし
