---
name: prompt_refactor_pocock
description: Architectural instructions and prompt refactoring eliminating No-Ops via an in-memory 3-stage cascade.
---

# Matt Pocock Prompt & Instructions Refactor

Structured pattern to eliminate token bleed, attention thinning, and sedimented No-Ops in agent instructions.

## 1. Core Concepts
* **No-Op Elimination:** If removing an instruction does not alter agent behavior or relax constraints, remove it entirely.
* **Ladder of Disclosure:**
  1. *In-file step:* Immediate procedural action.
  2. *In-file reference:* Flat local validation criteria.
  3. *Disclosed reference:* Detailed standards in external docs (`CODING_STANDARDS.md`), loaded only on demand.

## 2. In-Memory 3-Role Cascade
1. **Role 1 (Conservative Audit):** Clean syntax, dead links, and dead references without removing active rules.
2. **Role 2 (Modularity & Disclosure):** Extract bulky guidelines to external standards; leave concise context pointers.
3. **Role 3 (L0 Compression):** Eliminate No-Ops, collapse prose into leading keywords, retain hard stop-gates.

## 3. Safety & Commit Invariant
* **In-Memory Transformation:** Cascade runs strictly over text buffers in memory. Subagents receive no write permissions.
* **Failure Protocol:** If any stage fails validation or breaks links, trigger `BLOCK -> STOP -> RECORD EVIDENCE`. No blind rollbacks.
* **Two-Phase Commit:** Writing the final diff to disk requires an isolated, explicitly approved turn.
