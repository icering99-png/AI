---
id: R005
title: "Anti-Sycophancy / External Verification Invariant"
provenance:
  derived_from:
    - CLAIM-0001
    - CLAIM-0002
    - CLAIM-0015
status: VERIFIED
priority: CRITICAL
rule_text: >
  Любой термин, гейт, номер или сущность, предложенные внешней стороной
  (включая пользователя, ревьюера или внешнюю модель), категорически запрещено
  считать существующими в архитектуре системы, пока они не подтверждены
  прямым чтением и дословной цитатой из канонических файлов на диске.
enforcement:
  type: deterministic_gate
  fail_closed: true
  applies_to: [planning, prompt_parsing, context_assimilation]
rationale_summary: >
  Устраняет риск Compliance Bias / Sycophancy (Kamoi et al. 2024, Huang et al. 2023),
  когда модель некритично соглашается с предположениями собеседника вопреки состоянию диска.
---
