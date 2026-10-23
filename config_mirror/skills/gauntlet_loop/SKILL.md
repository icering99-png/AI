---
name: gauntlet_loop
description: Iterative self-refinement workflow using an isolated Fresh-Context Critic and the 8 principles of Matt Shumer.
---

# Gauntlet Loop Methodology

Autonomous quality refinement pattern for complex or long-running tasks.

## 1. Core Principles
1. **Actual Agent Environment:** Execute directly in a fully-equipped agent environment.
2. **Goal Over Implementation:** Specify target outcomes and quality metrics, not micro-steps.
3. **Real Quality Bar:** Provide concrete reference standards or test suites.
4. **Autonomous Decomposition:** Allow the lead agent to partition independent modules.
5. **Fresh-Context Critic:** Implementer never evaluates self; critic holds a clean context.
6. **Iterate to Completion:** Allow multiple refinement cycles without manual intervention.
7. **Watch Without Interrupting:** Intervene only if safety barriers or budgets are breached.
8. **Final Smoothing Pass:** Harmonize interfaces and cohesion once all components pass.

## 2. Invariants & Termination
* **Gate 6 Alignment:** The critic adheres strictly to "Critic Never Repairs" (`enable_write_tools = false`).
* **Smoothing Pass Gate:** Upon DAG completion, run whole-system integrity pass (`IntegrityGuard`, unlinked dead code, cross-import consistency).
* **Exit Condition:** Autonomous loop terminates only on deterministic `PASS` verdict from `RulesCritic` or escalation at retry budget limit.

