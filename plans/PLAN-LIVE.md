# plans/PLAN-LIVE.md — Active Execution Plan (Execution Locked)

## Metadata
* **Plan ID:** `PLAN-REWRITE-AGENTS-01`
* **Status:** `PENDING_APPROVAL`
* **Sanction Source Invariant:** Sanctioned via user request to rewrite AGENTS.md into a clean 40–80 line "README for agents".
* **Auto-Plan on Disk:** Gate 1 compliant autonomous recording.
* **Code Modification Lock:** LOCKED (Waiting for `APPROVE PLAN-REWRITE-AGENTS-01`)
* **Violation Policy:** Fail-Closed (`BLOCK -> STOP -> RECORD EVIDENCE`).
* **Objective:** Полная замена громоздкого `AGENTS.md` (нагромождение стоп-гейтов, дефектов спаррингов, битых ссылок и жаргона) на лаконичный практический гайд «README для агентов» (40–80 строк).
* **Allowed Paths:** `AGENTS.md`
* **Response Protocol Invariant (FAIL-0012):** L1 STE-100 summary in Russian, L2 Mermaid graph, L3 Human parameters table.
* **Language Invariant for Plan:** Step descriptions in clear Russian; metadata in English.

---

## Active Step
* **ID:** `SUB-01-REWRITE-AGENTS-GUIDE`
* **Status:** `PENDING_APPROVAL`
* **File:** `AGENTS.md`
* **Intent:** Переписать `AGENTS.md` в соответствии с требованиями: 54 строки, 5 ключевых разделов (Что за проект, Как запустить/проверить, Стиль кода в 7 пунктах, Что нельзя трогать, Что считается «готово»), без жаргона и номеров дефектов.
* **Allowed Paths:** `AGENTS.md`
* **Oracle / Test:** `DocGuard.audit_doc("AGENTS.md")` (0 битых ссылок); `python -m unittest discover tests` (169/169 PASS).

---

## Completed Steps
* (Нет)

---

## Pending Steps DAG
* `SUB-01-REWRITE-AGENTS-GUIDE`: Переписать `AGENTS.md` -> Валидация DocGuard -> Полный прогон тестов -> Отчет.
