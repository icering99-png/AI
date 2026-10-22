# AGENTS.md — Universal Agent Contract & Gateway Index (L0 Root)

> **Status:** Single Entry Point for any LLM and Agent Orchestrator.  
> **Invariant:** Reading this file provides the strict contract and stop-gates index. Detailed standards are loaded strictly on demand.

---

## 1. Fundamental Contract

* **User provides:** WHAT TO DO (Goal) + Resources / Constraints.
* **AI autonomously guarantees:** HOW + WHERE + SAFETY + VALIDATION + PROOF OF WORK.
* **Response Language Invariant:** Always communicate with the USER in Russian unless explicitly requested otherwise.
* **Storage Language Invariant:** All persistent architectural rules, logs, and failure records on disk MUST be authored strictly in English to minimize token overhead. Plan step descriptions in `plans/PLAN-LIVE.md` MAY be authored in clear Russian for user comprehension, while metadata remains in English.
* **Single Source of Truth:** Files on disk, manifests, and golden references. Chat history is NOT a source of truth. Subjective confidence scores are prohibited. Promotion to golden is strictly via `Candidate -> Backup -> Golden`.

---

## 2. Session Bootstrap Sequence

Before executing any task, the agent MUST execute this bootstrap sequence:
1. **L3 — Session Bridge:** Read `HANDOFF.md` (current status, verified artifacts, next step).
2. **L1 — Architectural Context:** Read `DECISIONS.md` (accepted ADRs, rationale).
3. **L2 — Failure Memory:** Read `failure_index.json` (disproven options; never repeat them).
4. **Task Execution:** Proceed with task planning only after steps 1–3 are confirmed.

---

## 3. Ten Mandatory Hard Stop-Gates

* **Gate 1 [Auto-Plan On Disk & Code RO Lock]:** Any structured task or action plan MUST be immediately saved to `plans/PLAN-LIVE.md` on disk autonomously without waiting for approval. Code modifications remain locked in Read-Only mode until explicit plan authorization via `APPROVE <PLAN-ID>` (Autonomous Batch Mode; interactive per-step mode removed). Chaining plan drafting with immediate unapproved edit in the same turn is prohibited (FAIL-0007).
* **Gate 2 [Batch Autonomous DAG & Atomic Steps]:** 1 step = 1 file, 1 intent, strictly within `allowed_paths`. The agent autonomously executes the sequential DAG (`verify -> RAW -> test -> next step`) end-to-end without per-step turn halts, yielding upon plan completion or test failure. Opportunistic side-fixes prohibited.
* **Gate 3 [No Big-Bang Rewrite]:** Complete module rewrite from scratch prohibited (Strangler Fig pattern).
* **Gate 4 [Proof of Work & Strict Evidence]:** Success recognized only via raw console output (`raw stdout`, `exit_code: 0`, passing tests). Active Tactile Verification (ITV): File, AST, Execution, and Subprocess probes mandatory.
* **Gate 5 [Read After Write — RAW]:** Mandatory inspection of every modified or created file via `view_file` before reporting.
* **Gate 6 [Critic Never Repairs & Asymmetry Guard]:** Implementer never self-evaluates; verified by deterministic `DefenseGuard` and blind `RulesCritic` (JSON verdict via `schemas/critic_verdict.json`, rule R001). Asymmetry Invariant: Critic/Auditor role is strictly forced to `Model: 'pro'`; Author/Implementer is isolated in `Workspace: 'branch'`. Adversarial Sparring Protocol: On-demand (via user command e.g. 'спарринг/файт на X мин' or major subsystem integration) triggers a deep multi-agent penetration fight in `fite/` with 5-minute status checkpoints under P0 Sandbox Lock.
* **Gate 7 [Universal Short Slug Rule]:** Slugs for sessions, branches, and decision files <= 20 chars (except `test_*.py`).
* **Gate 8 [Resource, Token & Derive Guard]:** Sequential role execution; «Do not dump — derive» (unconstrained dumps banned, query via AST one-liners or bounded slices); external cloud escalation via micro-packet <= 300 chars JSON via `schemas/escalation_packet.json` (max 2 tries); full code dumps prohibited.
* **Gate 9 [Mandatory Auto-Handoff & Failure Ingestion]:** Recording session progress in `HANDOFF.md` performed autonomously without user prompt. All confirmed adversarial sparring defects (AUD-FITE) MUST be synthesized and ingested into `failure_index.json` as permanent Disproven Options upon round completion.
* **Gate 10 [Fail-Closed & Priority Scale]:** P0 (Sandbox/Security/Blocker) to P4 (Cosmetic) hierarchy. Any unauthorized action, ambiguity, oracle failure, or metric `null` triggers immediate `BLOCK` with step rollback and `UNRESOLVED` status.

---

## 4. Progressive Disclosure Navigator (On-Demand Knowledge Map)

Load specialized standards strictly on trigger:

| Document | Path | Loading Trigger | Purpose |
| :--- | :--- | :--- | :--- |
| **Coding Standards** | `rules/CODING_STANDARDS.md` | After `APPROVE <PLAN-ID>`, before write tools | Limits: diff <= 30 lines, func <= 40 lines, cyclomatic <= 7, typing, path sandbox |
| **AI Governance** | `rules/02_UNIVERSAL_AI_GOVERNANCE.md` | During planning (Gate 1), role disputes, failures | Full Gate 1–10 specs, role isolation, Fail-Closed protocol, Watchdog |
| **Architecture Plan** | `PLAN_EVIDENCE_BASED_ARCHITECTURE.md` | Designing new subsystems or modules | Traceability: `SOURCE -> CLAIM -> RULE -> POLICY -> GATE -> EVIDENCE -> STATE` |
| **Critic Verdict Schema** | `schemas/critic_verdict.json` | Running/verifying council verdicts (Gate 6) | Machine-readable schema for `PASS` / `REJECT` verdict |
| **Escalation Packet Schema**| `schemas/escalation_packet.json` | External escalation via Gemini (Gate 8) | Micro-packet schema <= 300 chars (`g`, `c`, `e`, `w`) |
| **Evidence Manifest** | `KnowledgeBase/manifest.yaml` | Creating or modifying rules and oracles | Registry of 10 verified scientific claim cards |
| **Core Rules** | `KnowledgeBase/rules/00_core/` | Validating logical constraints (R001, etc.) | Atomic formal core rules |
| **Quick Start** | `README.md` | Initial repo setup in a new environment | Environment and test execution guide |
