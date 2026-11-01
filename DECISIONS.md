# Architecture Decision Log (DECISIONS.md)

## Active Architectural Baseline
* **L0–L3 Memory Architecture:** L0 Constitution (`AGENTS.md`), L1 Architecture (`DECISIONS.md`), L2 Failure Index (`failure_index.json`), L3 Bridge (`HANDOFF.md`).
* **Tier 0 Deterministic Gate:** Static AST verification, identifier length <= 15 chars, diff budget <= 30 LOC (`core/defense_guard.py`).
* **PreToolUse Security Gate:** System lifecycle hook intercepting tool calls via `.agents/hooks.json` and `core/pre_tool_guard.py`.
* **Independent Verification:** Read-only `RulesCritic` with canary traps, zero self-evaluation by implementer.
* **Offline-First & Escalation:** Local Ollama repair loop (`qwen2.5-coder`), Gate 8 micro-packet (`<= 300` chars via `schemas/escalation_packet.json`) to cloud gateway.
* **Execution Model:** Autonomous Batch DAG mode under approved disk plan (`plans/PLAN-LIVE.md`), turn-yield single-target invariant.

| Milestone / ADRs | Epoch | Key Focus | Status |
| :--- | :--- | :--- | :--- |
| **ADR-001..010** | Oct 2026 | Foundation: Governance, AST gates, Ollama integration, resource thresholds. | Accepted (baseline) |
| **ADR-011..020** | Oct 2026 | Reliability: NetGuard outbox, LadderGuard, TrustedFetch, PreToolUse hooks. | Accepted (baseline) |
| **ADR-021..026** | Oct 2026 | Security & Batch DAG: Anti-downgrade runner, CrashRecovery, FTS5 memory. | Accepted (active) |
| **ADR-027** | Oct 2026 | Remote Gateway & Vision: Multi-user sandboxes, clean access control (/allow, /deny), pure Multimodal Vision recognition. | Accepted (active) |

---
*Full detailed decision history (ADR-001..ADR-026 with contexts and rejected alternatives) is preserved in `git log DECISIONS.md`.*
*To inspect historical records: `git log -p DECISIONS.md`.*
