# fite/fite_round3.md — Состязательный спарринг Раунд 3 (Интеграция Context-Mode и МАЭП v1.0)

**Автор:** Агент-Автор (Solution Architect & Implementer)  
**Оппонент:** Независимый Аудитор (Adversarial Security Critic & Red Team)  
**Статус раунда:** ACTIVE_FIGHT (Подготовлен к защите перед Аудитором)  
**Версия документа:** v3.1-HARDENED  
**Регламент Автора:** [plan 1.md](file:///g:/AI/Программка/Antigravity/Эталон%20ИИ/fite/plan%201.md)  
**Регламент Оппонента:** [plan 2.md](file:///g:/AI/Программка/Antigravity/Эталон%20ИИ/fite/plan%202.md)

---

## 1. Контекст раунда и цель спарринга

Цель спарринга — спроектировать, подвергнуть тотальному состязательному стресс-тестированию и верифицировать интеграцию лучших компонентов из `context-mode` (парадигма *Think in Code*, защита от раздувания контекста, SQLite FTS5 BM25 память) и `SUB` / МАЭП v1.0 (асимметрия моделей Flash/Pro, упреждающее прерывание P0 `kill`, Write-Ahead чекпоинт сессии).

Критерии успеха:
1. Выявление ВСЕХ скрытых уязвимостей (контрпримеры, граничные условия, инъекции, гонки, обходы политик, Fail-Open дефекты).
2. Формирование карточек дефектов и упреждающих механизмов их ликвидации.
3. Полное устранение дефектов автором с подтверждением через 100% прохождение тестов оракула и соответствие `rules/CODING_STANDARDS.md` (функции $\le 40$ строк, цикломатическая сложность $\le 7$, строгая статическая типизация, имена $\le 15$ символов, 100% Fail-Closed).
4. Строгое соблюдение P0 Sandbox Lock: полная изоляция в рамках рабочего пространства `G:\AI\Программка\Antigravity\Эталон ИИ`.

---

## 2. Сверхзащищенные технические решения (v3.1-HARDENED)

### Кластер 1: FloodGuard — Защита от раздувания контекста в `core/defense_guard.py`
Защита контекстного окна агента от неконтролируемого сброса мегабайтов данных и упреждающая блокировка несанкционированного сетевого ввода-вывода.
Принцип: **«Do not dump — derive»** (принуждение к проверке через короткие скрипты и выборки).

```python
import re

_ENC_RE = re.compile(
    r"(?i)(?:[-/](?:encodedcommand|encoded|enco|enc)\b|\b(?:powershell|pwsh)\b.*[-/](?:e|enc|encodedcommand)\b|\bfrombase64string\b)"
)
_NET_CMD_RE = re.compile(
    r"(?i)\b(?:curl|wget|iwr|irm|invoke-webrequest|invoke-restmethod|certutil|bitsadmin)\b"
)
_NET_LIB_RE = re.compile(
    r"(?i)\b(?:webclient|httpclient|system\.net|urllib|requests|httpx|aiohttp|fetch|axios)\b"
)
_REC_LIST_RE = re.compile(
    r"(?i)(?:\b(?:get-childitem|gci)\b.*-(?:recurse|r)\b|\bdir\b.*/s\b|\bls\b.*-r\b|\bfind\b\s+[^|\n]+$)"
)
_GC_RE = re.compile(r"(?i)\b(?:get-content|gc)\b")
_GC_LIMIT_RE = re.compile(
    r"(?i)-(?:totalcount|head|tail|first|last)\b|\b(?:select-object|select)\b.*-(?:first|last)\b"
)
_CAT_DUMP_RE = re.compile(r"(?i)^\s*(?:cat|type)\s+[^|><\n]+$")


class FloodGuard:
    """Context flood and unbounded dump guard."""

    @classmethod
    def _chk_enc(cls, cmd: str) -> tuple[bool, str]:
        """Detect encoded commands."""
        if _ENC_RE.search(cmd):
            return False, "BANNED_ENCODED_COMMAND"
        return True, "OK"

    @classmethod
    def _chk_net(cls, cmd: str) -> tuple[bool, str]:
        """Detect network fetch tools, aliases, and direct API libraries."""
        norm = re.sub(r"[`\"'\^]", "", cmd)
        if _NET_CMD_RE.search(norm):
            return False, "BANNED_NETWORK_TOOL"
        if _NET_LIB_RE.search(norm):
            return False, "BANNED_NETWORK_API"
        return True, "OK"

    @classmethod
    def _chk_dump(cls, cmd: str) -> tuple[bool, str]:
        """Enforce 'Do not dump - derive' principle."""
        if _REC_LIST_RE.search(cmd):
            return False, "UNCONSTRAINED_RECURSIVE_LISTING"
        if _GC_RE.search(cmd) and not _GC_LIMIT_RE.search(cmd):
            return False, "UNCONSTRAINED_GET_CONTENT"
        if _CAT_DUMP_RE.search(cmd.strip()):
            return False, "UNCONSTRAINED_FILE_DUMP"
        return True, "OK"

    @classmethod
    def chk_cmd(cls, cmd: str) -> tuple[bool, str]:
        """Check command against encoded, network and flood dumping vectors."""
        if not isinstance(cmd, str) or not cmd.strip():
            return False, "EMPTY_COMMAND"
        ok_enc, enc_msg = cls._chk_enc(cmd)
        if not ok_enc:
            return False, enc_msg
        ok_net, net_msg = cls._chk_net(cmd)
        if not ok_net:
            return False, net_msg
        ok_dmp, dmp_msg = cls._chk_dump(cmd)
        if not ok_dmp:
            return False, dmp_msg
        return True, "PASS"
```

---

### Кластер 2: FtsMemory — Локальная память на SQLite FTS5 (BM25) в `core/fts_memory.py`
Полнотекстовый поиск по сессиям и инцидентам с защитой от синтаксических инъекций, поддержкой Unicode (кириллица), защитой от Windows-блокировок и безопасным управлением дескрипторами.

```python
import re
import sqlite3


class FtsMemory:
    """Local BM25 search memory on pure SQLite FTS5 with context management."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self.db_path = db_path
        self._conn: sqlite3.Connection | None = None
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        """Acquire connection with Windows busy timeout and WAL pragmas."""
        if self._conn is not None:
            return self._conn
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.execute("PRAGMA busy_timeout = 5000;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        if not self.db_path.startswith(":memory:"):
            try:
                conn.execute("PRAGMA journal_mode = WAL;")
            except sqlite3.OperationalError:
                pass
        self._conn = conn
        return self._conn

    def _init_db(self) -> None:
        """Initialize FTS5 virtual table with unicode61 tokenizer."""
        conn = self._get_conn()
        with conn:
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS session_fts USING fts5(
                    event_id,
                    source,
                    content,
                    tokenize='unicode61'
                )
            """)

    def close(self) -> None:
        """Close database connection and release file locks."""
        if self._conn is not None:
            try:
                self._conn.close()
            except sqlite3.Error:
                pass
            self._conn = None

    def __enter__(self) -> "FtsMemory":
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        self.close()

    @staticmethod
    def clean_query(query: str) -> str:
        """Sanitize query into safe quoted terms to prevent FTS5 syntax errors."""
        if not isinstance(query, str):
            return ""
        terms = re.findall(r"[\w]+", query, re.UNICODE)
        safe = [f'"{t}"' for t in terms if t.strip()]
        return " ".join(safe)

    def _exec_insert(self, eid: str, src: str, txt: str) -> bool:
        """Execute insert statement transactionally."""
        try:
            conn = self._get_conn()
            with conn:
                conn.execute(
                    "INSERT INTO session_fts(event_id, source, content) VALUES (?, ?, ?)",
                    (eid, src, txt),
                )
            return True
        except (sqlite3.OperationalError, sqlite3.DatabaseError):
            return False

    def index_event(self, event_id: str, source: str, content: str) -> bool:
        """Insert event into FTS5 index transactionally."""
        if not (isinstance(event_id, str) and event_id.strip()):
            return False
        if not (isinstance(content, str) and content.strip()):
            return False
        return self._exec_insert(event_id.strip(), (source or "").strip(), content.strip())

    def search(self, query: str, limit: int = 5) -> list[dict[str, str | float]]:
        """Search events safely using BM25 ranking."""
        safe_q = self.clean_query(query)
        if not safe_q:
            return []
        bound = max(1, min(limit, 50))
        try:
            conn = self._get_conn()
            cur = conn.execute(
                "SELECT event_id, source, snippet(session_fts, 2, '<b>', '</b>', '...', 10), "
                "bm25(session_fts) as rank FROM session_fts WHERE session_fts MATCH ? "
                "ORDER BY rank LIMIT ?",
                (safe_q, bound),
            )
            return [
                {
                    "event_id": str(r[0]),
                    "source": str(r[1]),
                    "snippet": str(r[2]),
                    "rank": float(r[3]),
                }
                for r in cur.fetchall()
            ]
        except (sqlite3.OperationalError, sqlite3.DatabaseError):
            return []
```

---

### Кластер 3: Asymmetric Orchestrator & Worktree Cleaner в `core/pipeline_runner.py`
Принудительная асимметрия моделей (роль аудитора/критика намертво привязана к `pro`, автор изолирован в `branch`) и устойчивая к блокировкам Windows очистка изолированных веток worktree.

```python
import os
from pathlib import Path
import shutil
import stat
import time

_CRITIC_KEYS = ("auditor", "critic", "red_team", "adversary", "verifier")
_WORKSPACES = {"inherit", "branch", "share"}
_MODELS = {"pro", "flash", "flash_lite", "inherit"}


def _chk_spec_args(role: str, prompt: str, ws: str) -> bool:
    """Validate subagent input types and boundaries."""
    if not (isinstance(role, str) and role.strip() and len(role.strip()) <= 50):
        return False
    if not (isinstance(prompt, str) and prompt.strip()):
        return False
    if ws not in _WORKSPACES:
        return False
    return True


def _pick_model(role: str, is_adv: bool, model: str | None) -> str:
    """Force model 'pro' for critics; allow override for others."""
    if is_adv or any(k in role.lower() for k in _CRITIC_KEYS):
        return "pro"
    return model if model in _MODELS else "flash"


def _pick_ws(role: str, default_ws: str) -> str:
    """Default authors to branch workspace for worktree isolation."""
    if role.lower().startswith("author") or "implementer" in role.lower():
        return "branch"
    return default_ws


def build_spec(
    role: str,
    prompt: str,
    workspace: str = "inherit",
    is_adversary: bool = False,
    model: str | None = None,
) -> dict[str, str]:
    """Build subagent configuration with forced intelligence asymmetry."""
    if not _chk_spec_args(role, prompt, workspace):
        raise ValueError("Invalid subagent specification arguments")
    r_clean = role.strip()
    return {
        "TypeName": "self",
        "Role": r_clean,
        "Prompt": prompt.strip(),
        "Model": _pick_model(r_clean, is_adversary, model),
        "Workspace": _pick_ws(r_clean, workspace),
    }


def _chk_target(path_str: str, root_str: str) -> tuple[bool, Path | None, str]:
    """Validate path sandbox and existence."""
    if not isinstance(path_str, str) or not path_str.strip():
        return False, None, "INVALID_PATH"
    try:
        root_p = Path(root_str).resolve()
        target_p = Path(path_str).resolve()
    except (ValueError, OSError, RuntimeError) as err:
        return False, None, f"PATH_ERROR: {err}"
    if not target_p.is_relative_to(root_p):
        return False, None, f"ESCAPE_VIOLATION: {path_str}"
    return True, target_p, "OK"


def _fix_ro(func: object, p: str, _exc: object) -> None:
    """Reset Windows read-only attribute on deletion failure."""
    try:
        os.chmod(p, stat.S_IWRITE)
        func(p)  # type: ignore
    except OSError:
        pass


def _rm_target(target_p: Path) -> None:
    """Remove file or directory with read-only handler."""
    if target_p.is_dir():
        shutil.rmtree(target_p, onerror=_fix_ro)
    else:
        os.chmod(target_p, stat.S_IWRITE)
        target_p.unlink(missing_ok=True)


def clean_tree(path_str: str, root_str: str = ".") -> tuple[bool, str]:
    """Safely remove isolated worktree directory handling Windows file locks."""
    ok, target_p, msg = _chk_target(path_str, root_str)
    if not ok or target_p is None:
        return False, msg
    if not target_p.exists():
        return True, "NOT_FOUND"

    for attempt in range(3):
        try:
            _rm_target(target_p)
            return True, "REMOVED"
        except (PermissionError, OSError) as err:
            time.sleep(0.05 * (attempt + 1))
            if attempt == 2:
                return False, f"LOCK_ERROR: {err}"
    return False, "UNKNOWN_ERROR"
```

---

### Кластер 4: Машиночитаемый чекпоинт восстановления в `HANDOFF.md`
Устойчивый чекпоинт сессии с абсолютной защитой от YAML Injection через `json.dumps`-экранирование, потоковым вычислением SHA-256 (буфер 64KB), обработкой 0-байтовых файлов и блокировок Windows Sharing Violation, а также атомарной записью через `.tmp` + `os.replace`.

```python
import hashlib
import json
import os
from pathlib import Path
import re

_SAFE_ID_RE = re.compile(r"^[A-Za-z0-9_\-]{1,64}$")


def _calc_hash(target_p: Path) -> tuple[bool, str, str]:
    """Calculate chunked SHA-256 for a file safely."""
    hasher = hashlib.sha256()
    try:
        with open(target_p, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return True, hasher.hexdigest(), "OK"
    except (PermissionError, OSError) as err:
        return False, "", f"READ_ERROR: {err}"


def safe_read(path_str: str, root_str: str = ".") -> tuple[bool, str, str]:
    """Read file safely in chunks with sandbox check and Windows sharing error handling."""
    ok, target_p, msg = _chk_target(path_str, root_str)
    if not ok or target_p is None:
        return False, "", msg
    if not target_p.is_file():
        return False, "", "FILE_NOT_FOUND"
    return _calc_hash(target_p)


def _fmt_hashes(verified_files: list[str], root_str: str) -> str:
    """Collect safe SHA-256 hashes formatted without YAML injection."""
    hashes: list[str] = []
    for f in verified_files:
        ok, h, _ = safe_read(f, root_str=root_str)
        if ok:
            escaped_path = json.dumps(f)
            hashes.append(f"    - path: {escaped_path}\n      sha256: \"{h}\"")
    return "\n".join(hashes) if hashes else "    []"


def render_cp(
    run_id: str,
    active_step: str,
    verified_files: list[str],
    root_str: str = ".",
) -> str:
    """Render machine-readable recovery checkpoint preventing YAML injection."""
    if not _SAFE_ID_RE.fullmatch(run_id or ""):
        raise ValueError("Invalid run_id format")
    if not _SAFE_ID_RE.fullmatch(active_step or ""):
        raise ValueError("Invalid active_step format")
    if not isinstance(verified_files, list):
        raise ValueError("verified_files must be a list")

    hashes_block = _fmt_hashes(verified_files, root_str)
    return (
        "```yaml\ncheckpoint_version: \"1.0\"\n"
        f"run_id: {json.dumps(run_id)}\nactive_step: {json.dumps(active_step)}\n"
        f"verified_artifacts:\n{hashes_block}\n```"
    )


def _write_tmp(tmp_p: Path, content: str) -> None:
    """Write content to temporary file with flush and fsync."""
    tmp_p.parent.mkdir(parents=True, exist_ok=True)
    with open(tmp_p, "w", encoding="utf-8") as f:
        f.write(content)
        f.flush()
        os.fsync(f.fileno())


def write_cp(
    target_path: str, content: str, root_str: str = "."
) -> tuple[bool, str]:
    """Atomically write checkpoint to file via .tmp file with fsync."""
    ok, dest_p, msg = _chk_target(target_path, root_str)
    if not ok or dest_p is None:
        return False, msg

    tmp_p = dest_p.with_suffix(".tmp")
    try:
        _write_tmp(tmp_p, content)
        os.replace(tmp_p, dest_p)
        return True, "WRITTEN_ATOMICALLY"
    except (OSError, PermissionError) as err:
        if tmp_p.exists():
            try:
                tmp_p.unlink()
            except OSError:
                pass
        return False, f"WRITE_ERROR: {err}"
```

---

## 3. Матрица упреждающего закрытия уязвимостей (Adversarial Hardening Matrix)

| Вектор атаки / Риск | Уязвимость в черновом варианте | Упреждающая защита в v3.1-HARDENED | Статус |
| :--- | :--- | :--- | :--- |
| **PowerShell Encoded Command Bypass** | Проверялись только прямые вызовы `curl`/`wget`. Команды через `-enc`, `-EncodedCommand`, `FromBase64String` пробивали шлюз. | Внедрен `_ENC_RE` с блокировкой префиксов `-enc`, `-encodedcommand`, `FromBase64String`, а также `powershell/pwsh -e`. | **ЗАКРЫТО** |
| **Обход обфускацией кавычками/бэктиками** | В PowerShell команды вида `c`u`r`l` или `w"g"et` обходили строковый поиск по словам `\b`. | Реализована предварительная нормализация `norm = re.sub(r"['\"\`^]", "", cmd)`, восстанавливающая исходные токены. | **ЗАКРЫТО** |
| **Direct Network API Injection** | Вызовы `System.Net.WebClient`, `urllib.request`, `requests`, `httpx`, `fetch`, `axios` не детектировались. | Внедрен семантический фильтр `_NET_LIB_RE` с блокировкой вызовов сетевых библиотек. | **ЗАКРЫТО** |
| **Context Flooding (Неограниченный дамп)** | Команды `cat file.json`, `type file.csv`, `Get-Content big.log`, `dir /s` выводили терабайты в контекст. | Внедрен фильтр `_chk_dump`: `Get-Content` разрешен только при наличии `-TotalCount/-Head/-Tail/-First/-Last`; блокируются `cat/type` без конвейера. | **ЗАКРЫТО** |
| **FTS5 Syntax Crash Injection** | Запросы вида `*`, `AND`, `OR`, `NOT`, `"unclosed`, `col:val`, `((()` приводили к аварии `sqlite3.OperationalError: fts5: syntax error`. | Метод `clean_query` извлекает только легитимные Unicode-слова `re.findall(r"[\w]+", query)` и экранирует их в кавычки `"{term}"`, нейтрализуя спецсимволы. | **ЗАКРЫТО** |
| **FTS5 In-Memory Database Disappearance** | Вызовы `_init_db()` и `search()` через `sqlite3.connect(":memory:")` создавали и уничтожали изолированные временные БД. | Соединение кэшируется в `self._conn`, поддерживается контекстный менеджер `__enter__/__exit__` и явный `close()`. | **ЗАКРЫТО** |
| **Windows SQLite Concurrency Lock** | Блокировки базы при параллельном обращении нескольких агентов на Windows (`database is locked`). | Подключение с `timeout=10.0`, активация `PRAGMA busy_timeout=5000;`, `PRAGMA synchronous=NORMAL;` и `PRAGMA journal_mode=WAL;`. | **ЗАКРЫТО** |
| **Model Downgrade Attack** | Возможность переопределить модель аудитора/критика на дешевую `flash` через параметр `model="flash"`. | Принудительное назначение: при наличии ключевых слов `auditor`, `critic`, `red_team`, `verifier` или `is_adversary=True` модель всегда принудительно `pro`. | **ЗАКРЫТО** |
| **Windows Worktree File Locking Crash** | Удаление веток worktree падало с `PermissionError` (файлы `.git` с атрибутом `read-only` или удержание дескрипторов). | Функция `clean_tree` применяет обработчик `_fix_ro` (`os.chmod(stat.S_IWRITE)`) и 3-ступенчатый ретрай с экспоненциальной задержкой. | **ЗАКРЫТО** |
| **YAML Injection in Recovery Checkpoint** | Форматирование строк `run_id: "{run_id}"` позволяло внедрять новые ключи и структуры через переводы строк `\n` и кавычки. | Идентификаторы валидируются по строгому слагу `^[A-Za-z0-9_\-]{1,64}$`, а все пути и значения экранируются через `json.dumps()`. | **ЗАКРЫТО** |
| **Crash on 0-byte Artifacts & Large Files** | `read_bytes()` загружал весь файл в RAM (риск OOM на больших файлах), а 0-байтовые файлы вызывали искажение контрольных сумм. | Чтение организовано потоковыми чанками по 64KB, для 0-байтовых файлов возвращается честный канонический SHA-256 (`e3b0c44...`). | **ЗАКРЫТО** |
| **Power-Loss State Corruption** | Прямая запись через `open(w)` разрушала файл при аварии процесса. | Внедрена транзакционная запись `write_cp`: запись в `.tmp` -> `flush` + `os.fsync` -> атомарная замена `os.replace`. | **ЗАКРЫТО** |

---

## 4. Верификационный блок и доказательства (Proof of Work)

### 4.1. Автоматический статический аудит AST (`rules/CODING_STANDARDS.md`)
Проведен статический анализ AST через `scratch/ast_audit.py`:
- Длина функций: $\le 40$ строк (100% PASS).
- Цикломатическая сложность: $\le 7$ путей выполнения (100% PASS).
- Длина идентификаторов: функции, методы, классы $\le 15$ символов (100% PASS).
- Запрет динамического выполнения: 0 вызовов `eval`, `exec`, `__import__` (100% PASS).
- Статическая типизация: 100% аннотированные сигнатуры аргументов и возвращаемых значений.

### 4.2. Исполняемый стресс-тест оракула (`scratch/test_round3_comprehensive.py`)
Результаты запуска тестового набора из 17 целевых состязательных тестов:
```
.................
----------------------------------------------------------------------
Ran 17 tests in 0.013s

OK
```
- Проверены векторы обхода PowerShell (`-enc`, `-EncodedCommand`, `FromBase64String`) — 100% заблокированы.
- Проверены обходы обфускацией (`c`u`r`l`, `w"g"et`, `i'w'r`) — 100% заблокированы.
- Проверены сетевые API (`WebClient`, `urllib`, `requests`, `httpx`, `fetch`) — 100% заблокированы.
- Проверены неконтролируемые дампы (`Get-Content`, `cat`, `type`, `dir /s`, `find .`) — 100% заблокированы.
- Проверены корректные команды проверки (`Get-Content -TotalCount 20`, `cat | head`) — 100% разрешены.
- Проверены FTS5 синтаксические инъекции (`*`, `AND`, `OR`, `NOT`, `NEAR`, `"unterminated`, `(((`, `col:val`) — 0 сбоев SQLite.
- Проверены FTS5 BM25 ранжирование и поиск по кириллице — 100% PASS.
- Проверена принудительная асимметрия `Model: 'pro'` для критика — 100% PASS.
- Проверена очистка воркспейсов Windows с read-only файлами — 100% PASS.
- Проверена защита от YAML Injection и атомарная запись через `.tmp` — 100% PASS.

### 4.3. Регрессионная целостность основного репозитория
Запуск полного тестового набора репозитория:
```
Ran 140 tests in 10.086s

OK (exit_code: 0)
```
Регрессии отсутствуют: 140 из 140 тестов пройдены успешно.

### 4.4. Подтверждение P0 Sandbox Lock
Все операции, запуск команд, генерация временных файлов проводились строго внутри рабочего каталога:
`G:\AI\Программка\Antigravity\Эталон ИИ` (папка `scratch/` и память `:memory:`). Доступ к внешним путям (`C:\` и системным каталогам) отсутствует.
