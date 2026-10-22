---
id: R003
title: "Cost Router Tiering / Look Before You Leap"
provenance:
  derived_from:
    - CLAIM-0004
    - CLAIM-0010
    - CLAIM-0016
status: VERIFIED
priority: HIGH
rule_text: >
  Любое обращение к внешним облачным вычислениям (Tier 3) строго запрещено
  до исчерпания дешевых детерминированных локальных оракулов (Tier 0: AST, regex, линтеры)
  и легковесных локальных попыток исправления (Tier 1/2). Эскалация разрешена только
  в виде структурированного микро-пакета <= 300 символов JSON при доказанном тупике.
enforcement:
  type: deterministic_gate
  fail_closed: true
  applies_to: [model_escalation, code_generation, cost_budget]
rationale_summary: >
  Снижает расточительство токенов, защищает от контекстных галлюцинаций
  и гарантирует соблюдение Gate 8 (Resource & Token Guard).
---
