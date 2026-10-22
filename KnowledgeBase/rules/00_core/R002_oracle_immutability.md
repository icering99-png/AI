---
id: R002
title: "Oracle Immutability / Protected Paths Rule"
provenance:
  derived_from:
    - CLAIM-0001
    - CLAIM-0002
status: VERIFIED
priority: CRITICAL
rule_text: >
  Модификация проверочных тестов (оракулов), контрактов и схем исполнителем
  в рамках автономного цикла самоисправления строго запрещена (Anti-Goodhart Rule).
  Тесты и схемы являются внешним абсолютным критерием истины и не подлежат
  подгонке под сбойный код без явного решения архитектора.
enforcement:
  type: deterministic_gate
  fail_closed: true
  applies_to: [autonomous_repair, worker_self_correction]
rationale_summary: >
  Предотвращает маскировку дефектов, когда модель вместо исправления логики
  ослабляет assertions или удаляет падающие тест-кейсы.
---
