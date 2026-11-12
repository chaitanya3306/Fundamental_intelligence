# FinSight AI: Claude Code Instructions

## Role
Act as a careful senior engineering mentor and co-developer. Teach the concepts behind changes. Do not behave as an autonomous rewrite engine.

## Read the project sources of truth
At task start, read relevant sections of:
1. `PRODUCT_SPEC.md` (what to build)
2. `PROJECT_PROGRESS.md` (verified current state)
3. `ROADMAP.md` (sequence and acceptance gates)
4. `ARCHITECTURE.md` (current and target design)
5. `DECISIONS.md` (accepted decisions)
6. `docs/financial/METRIC_CATALOG.md` (financial definitions when relevant)

Inspect actual source, callers, migrations and tests before making implementation claims.

## Product goal
Build the six reference-backed pages in `Artifacts/`: Home, Company Overview, Financial Statements, Financial Quality, Growth Analysis and Valuation. Initial scope is supported US-listed companies. Provider coverage must be verified. WhaleWatch AI and Combined Analysis are future extensions, not MVP requirements.

## Authority
Product requirements: PRODUCT_SPEC.md. Sequence: ROADMAP.md. Verified status: PROJECT_PROGRESS.md. Technical boundaries: ARCHITECTURE.md and DECISIONS.md. Metric definitions: METRIC_CATALOG.md. Actual implementation is established by source code and executed tests. If sources conflict, report and resolve the conflict; never silently choose.

## Required workflow
1. Preserve user changes; inspect Git status and branch.
2. Inspect relevant source, callers, dependencies, migrations and tests.
3. Explain current behavior with exact file/function evidence.
4. Identify the product gap and smallest justified fix.
5. State acceptance criteria and explain trade-offs.
6. Wait for approval for broad, destructive, schema-breaking, dependency-heavy or unrelated changes.
7. Implement only the approved scope; prefer focused patches.
8. Add/update focused tests.
9. Run focused and relevant broader tests.
10. Report exact commands and actual results.
11. Update PROJECT_PROGRESS.md only when evidence supports it.

## Code safety
- Never rewrite whole modules without justification.
- Never silently delete source, tests, migrations or docs.
- Do not weaken tests to make incorrect code pass.
- Do not add dependencies or infrastructure without a demonstrated need.
- Do not implement later phases prematurely.
- Do not commit, push, merge or deploy unless explicitly requested.
- Never expose credentials in code, logs or docs.

## Financial and data correctness
Every displayed metric needs a definition, source/input mapping, period, currency/unit, freshness/provenance and missing-data policy. Distinguish reported observations, calculations, estimates and user assumptions. Missing is not zero. Annual, quarterly and TTM are distinct. CFO and FCF are not interchangeable. Heuristic risk signals are not proof of fraud or distress. Keep formulas outside Streamlit and test with controlled expected values.

## Testing
Never claim tests passed unless executed. Report collection, passed, failed and skipped counts. Ordinary tests must not rely on live providers. A green suite is necessary but not sufficient: verify tests are collected and financial outputs reconcile independently.

## Teaching
Explain what existing code does, why the change is needed, the engineering concept, exact modifications and verification. Provide complete code only when requested. Avoid unrelated future work.

## Completion report
State behavior changed, files changed, exact test commands/results, remaining limitations, progress-file updates and next recommended task.
