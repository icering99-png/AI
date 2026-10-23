---
id: R004
title: "Asymmetric Arbitration / Auditor vs Defense"
provenance:
  derived_from:
    - CLAIM-0005
    - CLAIM-0015
status: VERIFIED
priority: CRITICAL
rule_text: >
  При разногласиях между детерминированным оракулом (Auditor-Rules) и состязательным
  агентом (Auditor-Defense) применяется асимметричный арбитраж: вердикт REJECT от Rules
  является абсолютным блокирующим отказом (Fail-Closed, Gate 10); вердикт REJECT от Defense
  требует эскалации и обязательной фиксации рисков, но не может быть преодолен устным согласием.
enforcement:
  type: deterministic_gate
  fail_closed: true
  applies_to: [arbitration, council_verdict, multi_agent_review]
rationale_summary: >
  Детерминированные правила (контракты, AST, схемы) непреодолимы. Состязательный агент
  защищает от семантических и логических уязвимостей, отсекая чрезмерные полномочия.
---
