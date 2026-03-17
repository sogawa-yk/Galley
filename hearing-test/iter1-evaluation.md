# Hearing Skill Evaluation Report - Iteration 1

## Test Input

**User Request**: 「在庫管理APIをPython/FastAPIで作りたい。Compute VMにデプロイしてATPデータベースを使いたい。パブリックIPで直接アクセスできるようにしたい。技術検証用です。」

**Scenario**: Technical PoC for an inventory management API

---

## Phase-by-Phase Evaluation

### Phase 1: 要望解析 (Request Analysis)

**Clarity**: 4/5
**Completeness**: 3/5
**Correctness**: 4/5

**Extracted values from user request**:
| Field | Extracted Value | Source Text |
|---|---|---|
| app_type | api | 「在庫管理API」 |
| language | python | 「Python/FastAPIで」 |
| framework | fastapi | 「Python/FastAPIで」 |
| compute_type | compute | 「Compute VMにデプロイ」 |
| database.type | atp | 「ATPデータベースを使いたい」 |
| access_type | public | 「パブリックIPで直接アクセス」 |
| purpose | poc | 「技術検証用です」 |

**Issues Found**:

1. **AMBIGUITY: No guidance on how to map user text to enum values**. The skill says to extract values but does not provide a mapping table (e.g., "Compute VM" -> `compute_type: "compute"`). The result-schema.md has examples but does not cover all phrasings. For instance, "技術検証" maps to `"poc"` but this mapping is implicit -- the agent must infer it from the purpose question's option B text and the schema's example.

2. **MISSING GUIDANCE: Handling of `container` field during extraction**. The user says "Compute VM" which strongly implies `container: "none"`, but the skill's extraction rules don't address inferring container mode from compute type. The skill only says "コンピュート種別が Functions の場合、コンテナ化方式の質問は省略し `container: "functions"` を自動設定する" -- no equivalent rule for Compute implying no-container.

3. **AMBIGUITY: Category selection vs. field extraction**. Phase 1 step 3 says to "identify applicable categories" and step 4 says to "record already-clear information as extracted." These are two different tasks but their relationship is not clearly defined. Does identifying `database` as an applicable category happen because the user mentioned ATP, or because inventory management typically needs a database?

4. **MISSING: No explicit instruction to record extraction results**. The skill says "record as extracted" but does not specify WHERE or in what format. Should the agent write to a temporary file? Keep in memory? This is ambiguous for non-conversational execution contexts.

---

### Phase 2: 質問生成 (Question Generation)

**Clarity**: 3/5
**Completeness**: 3/5
**Correctness**: 4/5

**Questions generated**: 8 questions (5 from templates, 3 dynamic)
**Questions skipped**: 5 (app type, language, compute type, DB type, access method, demo purpose)

**Issues Found**:

5. **AMBIGUITY: "Demo purpose" extraction edge case**. The user said "技術検証用" which maps to purpose=poc. The demo purpose question (project_info category) should be skipped because purpose is extractable. However, the skill says "カテゴリの必要性のみが示されている場合は、詳細質問は省略しない." Is "技術検証用です" a specific value or just indicating the category? It seems specific enough to skip, but the rule is not clear on this boundary.

6. **CONTRADICTION: Container question vs. compute question relationship**. The skill says "コンテナ化方式" and "コンピュート種別" are "related but separate questions." When the user explicitly says "Compute VM", should the containerization question still be asked? The skill only has an auto-skip rule for Functions, not for Compute. In practice, Compute VM can run Docker containers OR run directly, so the question IS still valid -- but the skill should state this explicitly to prevent agents from incorrectly auto-skipping it.

7. **MISSING GUIDANCE: Dynamic question count**. The skill says "最大5問まで" for dynamic questions but provides no minimum guidance. For this scenario I generated 3 dynamic questions (sample data, authentication, additional services). The "additional services" question is actually a template question (from additional_services category), not a dynamic question. The skill does not clarify whether template questions from conditional categories count toward the dynamic question limit.

8. **AMBIGUITY: Question numbering**. The skill's question format shows "## Question N" but does not specify whether N starts at 1 and is sequential across all categories, or restarts per category. I assumed sequential numbering.

9. **MISSING: Output path discrepancy**. The skill says to write to `hearing/questions.md`, but this test is writing to `hearing-test/` to avoid modifying the workspace. In a real scenario, the path `hearing/questions.md` is relative -- relative to what? The workspace root is implied but not stated.

10. **EDGE CASE: additional_services category activation**. The user request does not mention any additional services. Should the additional_services category be activated? The skill says it's "条件付き" (conditional) and activated "要望内容に応じて." For a PoC inventory API, it could go either way. I included it because it's a standard template question, but the skill provides no clear trigger criteria.

---

### Phase 3: 回答収集 (Answer Collection)

**Clarity**: 4/5
**Completeness**: 3/5
**Correctness**: 4/5

**Simulated answers**: All questions answered with reasonable PoC defaults (see iter1-questions.md).

**Issues Found**:

11. **MISSING: Handling of multi-select answers**. The additional_services question says "複数選択可、カンマ区切りで回答" but the standard answer format only has `[Answer]:` with a single value. The skill's answer validation in Phase 3 says "選択肢の文字（A, B, C...）以外の自由記述も有効な回答として受け付けます" which would cover "A, D" but this is not explicit.

12. **MISSING: How to handle "A" (auto-generate) for project name**. If the user selects "A" for the project name question, the agent must auto-generate a name. But this happens in Phase 5 (project_name rules). The flow between Phase 3 (collecting answer "A") and Phase 5 (generating the name) is implicit.

13. **EDGE CASE: File change detection**. Phase 3 says "ファイルが変更されていない場合はユーザーに再確認してください." How should the agent detect file changes? By comparing timestamps? Content hash? This is implementation-dependent and not specified.

---

### Phase 4: 矛盾検出 (Contradiction Detection)

**Clarity**: 4/5
**Completeness**: 4/5
**Correctness**: 4/5

**Contradictions found in this scenario**: None.

**Issues Found**:

14. **POTENTIAL CONTRADICTION NOT COVERED**: The user requests "パブリックIPで直接アクセス" with ATP database. ATP by default is on a private subnet. The skill's contradiction patterns include "プライベートサブネットなのにパブリックIPを要求" but does NOT include the reverse case where public access to compute might still need private connectivity to ATP. This is a valid OCI architecture concern that the contradiction detection patterns don't cover.

15. **MISSING: Contradiction between extracted values and answered values**. What if a user's answer contradicts something extracted in Phase 1? For example, if Phase 1 extracted `compute_type: "compute"` from "Compute VM" but then a question answer implies OKE. The skill does not explicitly address cross-phase contradictions.

16. **AMBIGUITY: clarification file naming**. The skill says `hearing/clarification-{round}.md` but does not define what round number to start at. Is the first clarification round 1 or 2 (since the initial questions are "round 1")?

---

### Phase 5: 構造化出力 (Structured Output)

**Clarity**: 3/5
**Completeness**: 3/5
**Correctness**: 3/5

**Issues Found**:

17. **SCHEMA INCONSISTENCY: `container` field**. The `container` field is listed as a required field in hearing.md's Phase 5 (the required fields JSON block) but it is also listed as required in result-schema.md. However, the sample in result-schema.md includes `container: "docker"` but the required fields block in hearing.md does NOT list `container`. Looking more carefully: hearing.md lists 6 required fields (project_name, app_type, compute_type, compute_new_or_existing, language, framework). result-schema.md lists 8 required fields (adds `container` and `purpose`). **This is a contradiction** -- the two files disagree on which fields are required.

18. **MISSING: `purpose` field in hearing.md required fields**. hearing.md's Phase 5 required fields block does not include `purpose`, but result-schema.md lists it as required. The agent must reconcile this discrepancy.

19. **AMBIGUITY: subnet_type inference for "public" access**. The inference rule says `access_type: "public"` maps to `subnet_type: "public"`. But for Compute on a public subnet with direct public IP, should `load_balancer` be explicitly false? The skill doesn't say what the default for `load_balancer` is when access_type is "public" (not "lb_public").

20. **MISSING: Shape selection logic**. The sizing section in result-schema.md shows `"shape": "VM.Standard.E4.Flex"` as an example but the skill provides no guidance on how to select the shape. Is it always E4.Flex? Does it depend on compute_type? For Functions, there's no shape. This is unspecified.

21. **EDGE CASE: Empty additional_services**. When the user selects "E) 追加サービス不要", should the result have `"additional_services": []` (empty array) or should the field be omitted entirely? The schema says the field is "dynamic" (included only when applicable), which suggests omission, but including an empty array is also valid JSON.

22. **MISSING: Completion message format**. The Phase 5 completion message template uses `{project_name}` placeholder syntax but does not specify whether this is literal template syntax or just indicating where to substitute. Minor issue but could cause confusion.

---

## Summary Scores

| Phase | Clarity | Completeness | Correctness | Overall |
|---|---|---|---|---|
| Phase 1: 要望解析 | 4/5 | 3/5 | 4/5 | 3.7/5 |
| Phase 2: 質問生成 | 3/5 | 3/5 | 4/5 | 3.3/5 |
| Phase 3: 回答収集 | 4/5 | 3/5 | 4/5 | 3.7/5 |
| Phase 4: 矛盾検出 | 4/5 | 4/5 | 4/5 | 4.0/5 |
| Phase 5: 構造化出力 | 3/5 | 3/5 | 3/5 | 3.0/5 |
| **Overall Average** | **3.6** | **3.2** | **3.8** | **3.5/5** |

---

## Critical Issues (Must Fix)

1. **Required fields mismatch** (#17, #18): hearing.md and result-schema.md disagree on required fields. hearing.md omits `container` and `purpose` from its required fields block. This WILL cause inconsistent outputs depending on which file the agent prioritizes. **Fix**: Synchronize the required fields list in both files.

2. **No extraction-to-enum mapping table** (#1): The skill relies on implicit mapping from natural language to enum values. Different agents may produce different mappings. **Fix**: Add an explicit mapping table (e.g., "技術検証/PoC/検証" -> `"poc"`, "Compute/VM/仮想マシン" -> `"compute"`).

3. **Container auto-skip rules incomplete** (#6): Only Functions has an auto-skip/auto-set rule. Compute VM is ambiguous (can use Docker or not). **Fix**: Either add auto-skip rules for all compute types or explicitly state that the container question is always asked unless compute is Functions.

---

## Important Issues (Should Fix)

4. **OCI architecture contradiction not detected** (#14): Public compute + ATP needs consideration for network connectivity between public subnet compute and private ATP endpoint. **Fix**: Add a contradiction pattern for "public subnet compute + managed database connectivity."

5. **Dynamic vs. template question boundary unclear** (#7, #10): No clear criteria for when conditional-category template questions are activated vs. when dynamic questions are generated. **Fix**: Define explicit trigger conditions for each conditional category.

6. **Multi-select answer format** (#11): The standard question format doesn't accommodate multi-select cleanly. **Fix**: Either add a "multi-select" question variant or clarify that comma-separated values in [Answer]: are valid.

7. **Extraction recording mechanism unspecified** (#4): Where Phase 1 extraction results are stored is not defined. **Fix**: Specify that extracted values are held in working memory and written directly into result.json in Phase 5.

---

## Minor Issues (Nice to Fix)

8. **File path ambiguity** (#9): `hearing/` path is relative but base directory is not stated.
9. **Clarification round numbering** (#16): Starting round number not defined.
10. **Shape selection logic missing** (#20): No guidance on OCI shape selection.
11. **Empty array vs. field omission** (#21): No guidance on handling empty dynamic fields.
12. **Question numbering convention** (#8): Sequential vs. per-category not specified.
13. **load_balancer default for public access** (#19): Not explicitly set to false.
14. **Phase 3 file change detection** (#13): No mechanism specified.
15. **Cross-phase contradiction detection** (#15): Not addressed.

---

## Improvement Suggestions (Prioritized)

### P0 - Critical
1. Synchronize required fields between hearing.md Phase 5 and result-schema.md
2. Add explicit natural-language-to-enum mapping table in hearing.md or a separate reference file

### P1 - Important
3. Add comprehensive container auto-inference rules (not just Functions)
4. Add OCI-specific contradiction patterns (e.g., public compute + managed DB network path)
5. Define explicit activation triggers for conditional categories (database, network, additional_services)
6. Clarify multi-select answer handling

### P2 - Improvement
7. Specify extraction result storage mechanism
8. Define question numbering as globally sequential
9. Add default values table for optional fields (e.g., load_balancer defaults to false unless access_type is lb_public)
10. Add shape selection guidance per compute type
11. Clarify that relative file paths are relative to workspace root
12. Define clarification round numbering (starting at 1)

### P3 - Polish
13. Add examples of extraction for common phrasings
14. Add a "decision log" concept for transparency on why questions were skipped
15. Consider adding a validation step that checks result.json against result-schema.md programmatically
