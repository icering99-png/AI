# 02_UNIVERSAL_AI_GOVERNANCE.md — Global AI Engineering Governance Specification

> **Status:** Mandatory normative governance for AI agents and orchestrators.  
> **Core Principle:** Strict Evidence. Speculation and unverified assumptions are strictly prohibited.

---

## 1. Fundamental Interaction Contract & Single Source of Truth

* **User provides:** WHAT TO DO (Goal) + Resources / Constraints.
* **AI autonomously guarantees:** HOW + WHERE + SAFETY + VALIDATION + PROOF OF WORK.
* **Single Source of Truth:** Files on disk, manifests, and golden references. Chat history is NOT a source of truth. Subjective confidence scores are prohibited. Promotion to golden is strictly via `Candidate -> Backup -> Golden`.
* Repetitive prompting of baseline rules by the user is prohibited.

---

## 2. Mandatory Hard Stop-Gates

### [GATE 1 — Auto-Plan On Disk & Code RO Lock]
* **Auto-Plan on Disk Invariant:** Any action plan or structural task decomposition MUST be immediately written to `plans/PLAN-LIVE.md` on disk autonomously without waiting for user approval.
* **Code Modification Lock:** Code files remain strictly Read-Only. Realization of any code step is prohibited without explicit plan-level authorization via `APPROVE <PLAN-ID>` (Autonomous Batch Mode; interactive per-step mode removed). Chaining plan approval with code modification in the same turn is prohibited (FAIL-0007).
* **Plan Requirements:**
  1. `SCOPE`: Explicit list of target files and symbols.
  2. `DEPENDENCIES & RISKS`: Potential regressions and external impacts.
  3. `ATOMIC DAG`: Step-by-step DAG decomposition (Step -> Dep -> Checkpoint).
  4. `EXIT EVIDENCE`: Concrete verification commands (`exit_code: 0`, test suites).
* **Scope Drift:** Requiring files outside approved scope -> `PLAN_INVALIDATED` -> write lock -> return to Gate 1.

### [GATE 2 — Atomic DAG Execution (Batch Autonomous DAG)]
* **1 intent = 1 DAG node:** Each step solves strictly one isolated subtask.
* **Allowed Paths:** Modifications strictly bounded to files in current step.
* **No Side-Fixes:** Incidental issues logged to backlog/handoff, never fixed concurrently.
* **Execution Cycle:** `verify -> RAW -> test -> next step`. Autonomous continuous execution without per-step turn halts, proceeding strictly upon green test exit code (`exit_code: 0`).

### [GATE 3 — Anti-Rewrite Invariant (No Big-Bang Rewrite)]
* Overwriting functional modules from scratch is prohibited.
* Apply Strangler Fig pattern for incremental replacement with backwards compatibility.

### [GATE 4 — Proof of Work & Strict Evidence]
* Claiming completion or stability without raw console logs (`raw stdout`, `exit_code: 0`) is prohibited.
* "Worked once" != "Works reliably". Evidence is mandatory. Raw logs precede conclusions.
* **Active Tactile Verification (ITV):** File, AST, Execution, and Subprocess probes are mandatory for every modified or created unit.
* **Explicit Metric Protocol:** Any computed metric that returns `null` or fails measurement triggers immediate Gate 10 `BLOCK`.

### [GATE 5 — Read-After-Write Verification (RAW)]
* After creating or editing a file, the agent MUST inspect modified lines via `view_file` to eliminate truncated generation, syntax errors, and broken imports.

### [GATE 6 — Critic Isolation & Defense Guard (Critic Never Repairs)]
* Implementer (Worker) never self-evaluates code.
* Two-tier independent verification:
  1. **Defense Guard:** Deterministic static filter (AST syntax, type validation, `allowed_paths`, diff <= 30 LOC, prohibited calls per `rules/CODING_STANDARDS.md`).
  2. **Rules Critic:** Contract and rule validator. Strictly Read-Only; never mutates code (Rule R001).
* Verdict format: strictly machine-readable JSON via `schemas/critic_verdict.json` (`verdict` PASS/REJECT, `rule_id`, `evidence`, `required_change`).
* **Adversarial Sparring Protocol (Variant 1 — On-Demand & Major Subsystems):** Deploys independent subagents with Model `pro` (Critics) and `branch` workspace (Authors) in `fite/`. Triggered on-demand (e.g. user prompt 'спарринг/файт на X мин') or upon major architectural integrations. Enforces 5-minute periodic status updates and strict P0 Sandbox Lock.

### [GATE 7 — Universal Short Slug Rule]
* All identifiers for sessions, branches, handoff cards, and decision files <= 20 chars (excluding `test_*.py`).

### [GATE 8 — Resource & Token Guard]
* Sequential execution with cooldown intervals.
* **External Cloud Escalation (Gemini Router):** Full code dumps prohibited.
* **Micro-Packet Limit:** Serialized JSON <= 300 chars total via `schemas/escalation_packet.json` (`g`, `c`, `e`, `w`).
* **Retry Limit:** Maximum 2 escalation attempts (1 retry).
* **Payload Overflow (`PAYLOAD_OVERFLOW`):**
  * *Architecture/system errors:* Local rollback without cloud escalation (Fail-Closed).
  * *Compute intensive:* Isolated limit <= 1000 chars without repository source code.

### [GATE 9 — Mandatory Auto-Handoff & Failure Ingestion]
* Upon completing a milestone or sparring round, the agent autonomously updates `HANDOFF.md`, session cards, and failure records without user prompting.
* All confirmed adversarial sparring defects (`AUD-FITE`) MUST be synthesized into permanent Disproven Options in `failure_index.json` to prevent recurring regressions across future sessions.

### [GATE 10 — Fail-Closed Protocol]
* Any unauthorized action, ambiguity, oracle failure, or escalation exhaustion triggers immediate `BLOCK`.
* Rollback changes, assign `UNRESOLVED` status, and record incident in `failure_index.json`.

---

## 3. Four-Tier File Memory Architecture (L0 — L3)

1. **L0 — Constitution (`AGENTS.md`):** Immutable project laws, architecture boundaries, and gateway index.
2. **L1 — Architecture (`DECISIONS.md`):** Accepted ADR log (context, rationale, rejected alternatives).
3. **L2 — Failure Memory (`failure_index.json`):** Verified incidents, root causes, and disproven options.
4. **L3 — Session Bridge (`HANDOFF.md`):** Current status, verified artifacts, and immediate next step.

---

## 4. Process Supervision (Graceful Watchdog)

* **STALL:** No new stdout, but active IO/resources. Grace period provided; kill prohibited.
* **HANG:** Confirmed deadlock (0% CPU). Issue soft `terminate` first; escalate to `kill` only upon timeout.

---

## 5. Architectural Map Discipline

* Inspect existing canonical files before creating new modules.
* Modify canonical files rather than spawning duplicates.
* Parallel competing modules with similar names are strictly prohibited.

---

## 6. Agent Instruction Antipatterns (Prohibitions)

* **No Unverified External Links:** Instructions referencing unmounted external repositories are prohibited.
* **No Slang or Roleplay Forcing:** Prompt instructions forcing persona/slang degrade formal reasoning and are prohibited.
* **No Artificial Character Limits:** Restricting response lengths arbitrarily without DAG subplan fission is prohibited.
* **No Critic Instruction Leaks:** Authoring generation hints in instructions accessible to blind auditor roles is prohibited.
