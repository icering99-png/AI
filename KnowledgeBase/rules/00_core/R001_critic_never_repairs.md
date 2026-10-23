---
id: R001
title: "Critic Never Repairs / External Verification Required"
provenance:
  derived_from:
    - CLAIM-0001
    - CLAIM-0002
    - CLAIM-0007
    - CLAIM-0008
status: VERIFIED
priority: CRITICAL
rule_text: >
  Модель не имеет права одновременно оценивать и исправлять собственный
  результат в рамках одного вызова/роли. Исправление ошибки допустимо
  только на основе внешнего детерминированного сигнала (unit-тест,
  линтер, AST-валидатор, другой независимый агент с ролью Critic,
  выдающий только PASS/FAIL + evidence, без права правки кода).
  Самокоррекция без внешнего фидбека запрещена как ненадёжная.
enforcement:
  type: deterministic_gate
  fail_closed: true
  applies_to: [code_edit, architecture_decision, self_review]
rationale_summary: >
  4 независимых исследования (Huang et al. 2023, Kamoi et al. 2024,
  Madaan et al. Self-Refine 2023 — два отдельных эксперимента) показывают:
  LLM без внешнего фидбека не способна надёжно находить и исправлять
  собственные ошибки, в части случаев качество ухудшается после
  самокоррекции (94% неудач self-refine из-за ошибок самооценки,
  94% ложных "всё в порядке" без внешней проверки в математических задачах).
---
