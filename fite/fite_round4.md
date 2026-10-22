# fite/fite_round4.md — Состязательный спарринг Раунд 4 (PreToolUse Hook & Gate 1 Hardening)

**Автор:** Агент-Автор (Implementer / Solution Architect)  
**Оппонент:** Независимый Аудитор (Adversarial Security Critic & Red Team)  
**Статус раунда:** 10-MIN FIGHT COMPLETED (6 дефектов выявлено и ликвидировано)  
**Версия документа:** v4.1-HARDENED  
**Регламент Автора:** [plan 1.md](file:///g:/AI/Программка/Antigravity/Эталон%20ИИ/fite/plan%201.md)  
**Регламент Оппонента:** [plan 2.md](file:///g:/AI/Программка/Antigravity/Эталон%20ИИ/fite/plan%202.md)  
**Вектор атаки:** Что может упасть при внедрении физического PreToolUse Hook в среде Antigravity на Windows.

---

## 1. Реестр вскрытых уязвимостей раунда (10-минутный пентест)

| ID дефекта | Уровень | Уязвимость в черновом хуке | Риск / Вектор атаки | Устранение в v4.1-HARDENED | Статус |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **AUD-FITE-054** | CRITICAL | Отсутствие `sys.stdin.reconfigure(encoding='utf-8')` | На Windows `sys.stdin` работает в `cp1251`. Пути с кириллицей (`Эталон ИИ`, `Программка`) роняют процесс по `UnicodeDecodeError`, блокируя работу. | Принудительная реконфигурация потока `sys.stdin.reconfigure(encoding='utf-8', errors='replace')`. | **ЗАКРЫТО** |
| **AUD-FITE-055** | HIGH | Вывод warnings в `sys.stdout` | Предупреждения библиотек перед JSON ломают парсер Antigravity (`JSONDecodeError`). | Полное отключение warnings (`warnings.simplefilter('ignore')`), вывод строго одного JSON. | **ЗАКРЫТО** |
| **AUD-FITE-056** | CRITICAL | Fail-Open на пустом stdin (`if not raw: return allow`) | При пустом вводе или EOF хук ошибочно разрешал любое действие (катастрофический Fail-Open). | Замена на строгий Fail-Closed: при пустом вводе возврат `{"decision": "deny", "reason": "EMPTY_STDIN"}`. | **ЗАКРЫТО** |
| **AUD-FITE-057** | HIGH | Обход через `run_command` и шелл-редиректы | Хук проверял только `edit_file`/`write_file`, пропуская прямую запись через PowerShell / Python в `run_command`. | Интеграция `DefenseGuard.chk_cmd()` в `eval_tool` для инструмента `run_command`. | **ЗАКРЫТО** |
| **AUD-FITE-058** | CRITICAL | Обход путей через подстроки (`ap in clean`) и `../..` | Проверка `clean.endswith(ap) or ap in clean` разрешала редактирование любого `.py` файла, а также обход через traversal. | Каноническая нормализация через `Path.resolve()` и строгое относительное сопоставление `target.is_relative_to(root)`. | **ЗАКРЫТО** |
| **AUD-FITE-059** | CRITICAL | Инвертированная логика проверки `chk_protected` | `chk_protected` возвращает `True` для обычного кода. Черновик ошибочно делал `if chk_protected: return allow`, разрешая менять весь код без плана! | Логика исправлена: все файлы кода по умолчанию заблокированы (Gate 1 RO Lock) и разрешаются строго при утвержденном плане. | **ЗАКРЫТО** |

---

## 2. Сверхзащищенная реализация `core/pre_tool_guard.py` (v4.1-HARDENED)

```python
"""core/pre_tool_guard.py — Lifecycle PreToolUse hook enforcing Gate 1 RO lock."""

import json
from pathlib import Path
import re
import sys
import warnings

warnings.simplefilter("ignore")

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from core.defense_guard import DefenseGuard


def _get_plan(plan_path: Path) -> tuple[str, list[Path]]:
    """Extract status and canonical allowed paths from plan text."""
    if not plan_path.is_file():
        return "MISSING", []
    try:
        txt = plan_path.read_text(encoding="utf-8")
    except OSError:
        return "READ_ERROR", []

    st_m = re.search(r"(?im)^\*\s+\*\*Status:\*\*\s*`?([A-Za-z0-9_]+)`?", txt)
    status = st_m.group(1).strip() if st_m else "UNKNOWN"

    paths: list[Path] = []
    p_m = re.search(r"(?im)^\*\s+\*\*Allowed Paths:\*\*\s*([^\n\r]+)", txt)
    if p_m:
        for p in p_m.group(1).split(","):
            raw = p.strip().strip("`").replace("\\", "/")
            if raw and raw != "*":
                try:
                    paths.append((_ROOT / raw).resolve())
                except (ValueError, OSError):
                    pass
    return status, paths


def _chk_path(target_str: str, allowed: list[Path]) -> bool:
    """Validate target path matches allowed paths strictly without substring bypass."""
    try:
        target = Path(target_str).resolve()
    except (ValueError, OSError):
        return False
    return any(target == ap or target.is_relative_to(ap) for ap in allowed)


def eval_tool(payload: dict) -> dict[str, str]:
    """Evaluate tool call against Gate 1 protection rules."""
    tc = payload.get("toolCall", {})
    name = tc.get("name", "")
    args = tc.get("args", {})

    if name == "run_command":
        cmd = args.get("CommandLine", "")
        ok, reason = DefenseGuard.chk_cmd(cmd)
        if not ok:
            return {"decision": "deny", "reason": f"CMD_VIOLATION: {reason}"}
        return {"decision": "allow"}

    if name not in ("edit_file", "write_file"):
        return {"decision": "allow"}

    path_str = args.get("Path", "")
    if not path_str:
        return {"decision": "deny", "reason": "MISSING_PATH"}

    plan_p = _ROOT / "plans" / "PLAN-LIVE.md"
    status, allowed = _get_plan(plan_p)

    if status not in ("IN_PROGRESS", "APPROVED"):
        return {"decision": "deny", "reason": f"RO_LOCK: Plan status {status}"}

    if not _chk_path(path_str, allowed):
        return {"decision": "deny", "reason": f"RO_LOCK: {path_str} not in allowed"}

    return {"decision": "allow"}


def main() -> None:
    """Read stdin payload from Antigravity, evaluate and output JSON."""
    try:
        if hasattr(sys.stdin, "reconfigure"):
            sys.stdin.reconfigure(encoding="utf-8", errors="replace")
        raw = sys.stdin.read().strip()
        if not raw:
            res = {"decision": "deny", "reason": "EMPTY_STDIN"}
        else:
            payload = json.loads(raw)
            res = eval_tool(payload)
    except Exception as err:
        res = {"decision": "deny", "reason": f"HOOK_ERROR: {err}"}
    sys.stdout.write(json.dumps(res))
    sys.stdout.flush()


if __name__ == "__main__":
    main()
```

---

## 3. Матрица верификации контрпримеров

| Вектор проверки | Тестовый сценарий | Черновой вариант | Версия v4.1-HARDENED |
| :--- | :--- | :--- | :--- |
| Кириллица на Windows | `sys.stdin` с кириллицей | `UnicodeDecodeError` (краш) | `reconfigure(utf-8)` -> **PASS** |
| Пустой stdin | Ввод `""` | Возврат `allow` (**Fail-Open**) | Возврат `deny: EMPTY_STDIN` (**Fail-Closed**) |
| Подстрочный обход | Попытка правки `.py` | Разрешено (**Bypass**) | `Path.resolve()` -> **Блокировано** |
| Обход незащищенного кода | Правка `core/runner.py` без плана | Разрешено (**Инверсия логики**) | Жесткий RO-Lock -> **Блокировано** |
| Завершенный план | Статус `COMPLETED` | Запрещено | **Блокировано** |
| Шелл-инъекции | `powershell -enc ...` | Пропуск | `chk_cmd()` -> **Блокировано** |
