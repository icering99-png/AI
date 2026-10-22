# ПЛАН 2: УНИВЕРСАЛЬНЫЙ ПРОТОКОЛ НЕЗАВИСИМОГО ОППОНЕНТА (АУДИТОР / КРИТИК)
# Версия протокола: 1.0-Universal
# Назначение: Регламент состязательного анализа, поиска дефектов, контрпримеров и строгой верификации

---

## 1. Назначение и границы применимости

1. Данный документ определяет обязательный порядок работы **Агента-Оппонента (Агента B)**.
2. Цель Оппонента — не пассивное одобрение, а **состязательная проверка решения на прочность (Adversarial Testing)**:
   - Поиск скрытых дефектов, граничных условий и уязвимостей;
   - Формирование воспроизводимых контрпримеров и сценариев отказа;
   - Требование доказательств (Proof of Work) для каждого заявления Автора;
   - Предотвращение регрессий при внесении правок.
3. Протокол универсален: он применяется к коду, архитектуре, документации, алгоритмам и конфигурациям.

---

## 2. Инициализация контура проверки (Audit Session Header)

При старте сессии Агент B фиксирует параметры аудита:

```yaml
audit_instance:
  audit_id: "<Краткий идентификатор аудита, <= 20 символов>"
  target_artifact: "<Путь к проверяемому результату Автора>"
  reference_specs: ["<Путь к исходным требованиям и инвариантам>"]
  adversarial_vectors:
    - "boundary_values_and_overflow"
    - "concurrency_and_race_conditions"
    - "type_and_schema_mismatches"
    - "unhandled_exceptions_and_fail_open"
    - "security_sandbox_escape"
  audit_log_path: "plan 2.md"
```

---

## 3. Правила и когнитивные инварианты Оппонента

1. **Презумпция дефектности (Zero-Trust):** Никакое решение Автора не принимается на веру без независимой проверки. Текстовое заверение «работает стабильно» приравнивается к отсутствию доказательства.
2. **Разделение фактов и мнений:**
   - **CONFIRMED_DEFECT:** Дефект, доказанный воспроизводимым контрпримером, упавшим тестом или явным противоречием спецификации;
   - **HYPOTHESIS:** Потенциальный риск, требующий постановки проверочного эксперимента;
   - **STYLE_PREFERENCE:** Субъективное стилевое предпочтение (запрещено требовать переделки, если решение удовлетворяет стандартам).
3. **Запрет молчаливого изменения требований:** Оппонент обязан сверять решение строго с исходными критериями задачи. Запрещено произвольно вводить новые требования под видом «дефектов», если они не вытекают из надежности, безопасности или контракта.
4. **Принцип «Критик не чинит» (Critic Never Repairs):** Оппонент выявляет проблему, формулирует контрпример и минимальные критерии приёмки, но **не переписывает артефакт за Автора**.
5. **Запрет иллюзии совершенства:** Отсутствие найденных дефектов на текущем такте проверки означает лишь то, что примененные проверки не выявили аномалий, но не делает решение абсолютно безупречным.

---

## 4. Реестр замечаний и жизненный цикл дефекта

Каждая обнаруженная проблема регистрируется Оппонентом в таблице замечаний со следующей структурой:

| ID | Критичность | Тип замечания | Локация в артефакте | Наблюдение / Контрпример | Ожидаемое поведение | Способ верификации | Статус |
|:---|:---|:---|:---|:---|:---|:---|:---|
| AUD-FITE-001 | CRITICAL | CONFIRMED_DEFECT | Разделы 1, 2, 4, 5 (v0.1) | Полное отсутствие предметной постановки задачи и реализации. Все ключевые разделы содержали плейсхолдеры (`[точная формулировка...]`). | Заполнить спецификацию полными инженерными решениями по AUD-020..AUD-027. | Ревизия текста спецификации v2.0 и v2.2. | FIXED-VERIFIED |
| AUD-FITE-002 | CRITICAL | CONFIRMED_DEFECT | Раздел 7 (v0.1) | В таблице тестирования указаны сценарии, но ни один тест фактически не запускался (`Статус: NOT RUN`). | Разработать исполняемый верификационный блок тестов в самом артефакте. | Тестовый блок `test_security_audit_round2.py` выполнен (7/7 PASS). | FIXED-VERIFIED |
| AUD-FITE-003 | HIGH | CONFIRMED_DEFECT | Раздел 6 (v0.1) | В таблице ошибок для всех сценариев стояло «Не запускалось», а ожидаемое поведение абстрактно (`[поведение]`). | Специфицировать детерминированную обработку ошибок по протоколу Fail-Closed. | Описано и внедрено в кодовые блоки v2.2. | FIXED-VERIFIED |
| AUD-FITE-004 | HIGH | CONFIRMED_DEFECT | Разделы 8, 9 (v0.1) | Таблица «История версий» содержала плейсхолдеры `[время]`, раздел 8 не имел ссылок. | Связать разделы со ссылками на `plan 2.md` и точными таймштампами. | Зафиксированы версии v0.1..v2.5 с таймштампами. | FIXED-VERIFIED |
| AUD-FITE-005 | MEDIUM | CONFIRMED_DEFECT | Раздел 10 (v0.1) | Чеклист самопроверки содержал невыполненные пункты (`- [ ]`). | Проставить честные отметки после исправления дефектов. | Актуализировано в Разделе 5 `Fite.md`. | FIXED-VERIFIED |
| AUD-FITE-006 | HIGH | CONFIRMED_DEFECT | Раздел 2 (v2.0) | Обход неизменяемости логов через `allow_test_edit=True`. Любой токен позволял редактировать `logs/guard_audit.jsonl`. | Выделить `IMMUTABLE_LOGS = ("logs", "guard_audit.jsonl")` с абсолютным запретом редактирования. | Проверено: `logs/` отклоняется даже при валидном токене. | FIXED-VERIFIED |
| AUD-FITE-007 | HIGH | CONFIRMED_DEFECT | Решение 4 (v2.0) | Падение `abort_hypo` на 0-байтовых файлах `NamedTemporaryFile` при запуске существующих тестов. | Добавить условие `p.exists() and p.stat().st_size > 0`. | Совместимость с 0-байтовыми файлами подтверждена. | FIXED-VERIFIED |
| AUD-FITE-008 | CRITICAL | CONFIRMED_DEFECT | Решение 5 (v2.0) | Искажение путей через `lstrip("./")` в `TurnGuard.chk_diff`. Срезались начальные точки скрытых каталогов (`.agents/` -> `agents/`, `.gitignore` -> `gitignore`). | Использовать строго `Path(p).as_posix()` согласно требованию R-05. | Точные пути и относительные пути работают без искажения точек. | FIXED-VERIFIED |
| AUD-FITE-009 | HIGH | CONFIRMED_DEFECT | Решение 3 (v2.0) | Необработанные `ValueError` при Sandbox Escape в `SemanticMemory.save_tmpl`. | Обернуть вызовы в `try-except (SyntaxError, ValueError, OSError, TypeError)`. | Возвращает `False` по Fail-Closed. | FIXED-VERIFIED |
| AUD-FITE-010 | HIGH | CONFIRMED_DEFECT | Решение 5 (v2.0) | Потеря префиксов при ручной нормализации строк (`\` vs `/`). | Нормализация через `Path(f).as_posix()`. | Проверено на Windows и Posix путях. | FIXED-VERIFIED |
| AUD-FITE-011 | MEDIUM | CONFIRMED_DEFECT | Решение 7 (v2.0) | Потеря диагностических сообщений об ошибках Git в `BranchGuard._run_git`. | Возвращать `res.stdout.strip() if res.returncode == 0 else (res.stderr.strip() or res.stdout.strip())`. | Диагностика ошибок сохраняется при ненулевом коде возврата. | FIXED-VERIFIED |
| AUD-FITE-012 | MEDIUM | CONFIRMED_DEFECT | Решение 4 (v2.0) | Захардкоженная дата `"2026-10-17"` в `abort_hypo`. | Использовать `date.today().isoformat()`. | Динамические даты подтверждены. | FIXED-VERIFIED |
| AUD-FITE-013 | MEDIUM | CONFIRMED_DEFECT | Решение 6 (v2.0) | Экранирование кириллических символов в UTF-8 JSON манифеста. | Добавить `ensure_ascii=False`. | Кириллица сохраняется корректно. | FIXED-VERIFIED |
| AUD-FITE-014 | HIGH | CONFIRMED_DEFECT | Раздел 3 (v2.1) | Ложное заявление об исполнении тестов оракула. Импорт `from core.defense_guard import is_valid_token` падает с `ImportError`, так как ядро `core/` не модифицировано. | Добавить локальный fallback для изолированного прогона аудита. | Тесты запускаются и проходят как изолированно, так и интеграционно. | FIXED-VERIFIED |
| AUD-FITE-015 | HIGH | CONFIRMED_DEFECT | Решение 2 (v2.1) | Аварийное падение `chk_protected` при передаче `path_str=None` или `123`. | Добавить явную валидацию `if not isinstance(path_str, str) or not path_str.strip(): return False, "..."`. | `chk_protected(None)` и `chk_protected(123)` возвращают `False` без падений. | FIXED-VERIFIED |
| AUD-FITE-016 | CRITICAL | CONFIRMED_DEFECT | Решение 5 (v2.1) | Обход файла плана через суффикс `p.endswith("/plans/plan-live.md")` и ложная блокировка бюджета при дубликатах. | Исключить `endswith`, использовать строго `p != "plans/plan-live.md"` и дедуплицировать список. | Обход плана пресечен; повторы одного файла не вызывают ложный отказ. | FIXED-VERIFIED |
| AUD-FITE-017 | HIGH | CONFIRMED_DEFECT | Решение 3 (v2.1) | Необработанное исключение `TypeError` в `SemanticMemory.save_tmpl` при `code=None` или числах. | Добавить валидацию `if not isinstance(code, str): return False` и включить `TypeError` в `except`. | `save_tmpl("cat", "k", None)` возвращает `False` по Fail-Closed. | FIXED-VERIFIED |
| AUD-FITE-018 | HIGH | CONFIRMED_DEFECT | Решение 4 (v2.1) | Падение `abort_hypo` по `AttributeError` при `name=None` или `reason=None`. Преждевременное удаление ветки Git до записи в `failure_index.json`. | Валидация `isinstance(name, str)` и перенос операций Git строго после успешной записи `failure_index.json`. | Транзакционность и защита от `None` подтверждены тестами. | FIXED-VERIFIED |
| AUD-FITE-019 | MEDIUM | CONFIRMED_DEFECT | Решение 6 (v2.1) | Падение `RegressGuard.save_manifest` при `files=None` и незащищенный от сбоев хеширования цикл. | Добавить проверку `isinstance(files, (list, tuple, set))` и включить цикл хеширования в `try-except`. | `save_manifest(None, "out.json")` возвращает `False` без падения. | FIXED-VERIFIED |
| AUD-FITE-020 | MEDIUM | CONFIRMED_DEFECT | Решение 1 (v2.1) | Отсутствие проверки соответствия токена конкретному плану в `RunbookGen.update_spec`. Любой токен `APPROVE <ANY>` разблокировал обновление спеки. | Передавать `expected_plan` в `is_valid_token`. | Проверено: спека обновляется строго по токену целевого плана. | FIXED-VERIFIED |
| AUD-FITE-021 | CRITICAL | CONFIRMED_DEFECT | `Fite.md`: строки 192, 220 (`BranchGuard.abort_hypo`) | При передаче `reason` как исключения или числа (`abort_hypo("hypo", RuntimeError("err"))` или `500`), выражение `(reason or "").strip()` вызывает `AttributeError`. | Строгая валидация `isinstance(reason, str)` с безопасным `Fail-Closed` отказом (`return False`), либо безопасная строковая конверсия `str(reason).strip()[:100]`. | `BranchGuard.abort_hypo("hypo", RuntimeError("err"))` не должно выбрасывать необработанное исключение. | FIXED-VERIFIED |
| AUD-FITE-022 | HIGH | CONFIRMED_DEFECT | `Fite.md`: строки 218, 225-227 (`BranchGuard.abort_hypo`) | Коллизия ID и потеря записей L2-памяти: `clean_name` усекается до 10 символов, а ID строится по первым 8 (`clean_name[:8].upper()`). Для гипотез `feature_auth_token` и `feature_auth_oauth` ID идентичен (`FAIL-FEATURE_`). Вторая гипотеза молча отбрасывается. | Генерация ID должна включать хеш/дигест имени или уникальный счетчик/таймстемп. | Отклонение двух гипотез с совпадающим 8-символьным префиксом сохраняет обе записи в `failure_index.json`. | FIXED-VERIFIED |
| AUD-FITE-023 | HIGH | CONFIRMED_DEFECT | `Fite.md`: строки 238-240 (`BranchGuard.abort_hypo`) | Маскировка сбоя Git (`Fail-Open`): `abort_hypo` игнорирует возвращаемый код `cls._run_git(["checkout", "-f", main_br])`. Если checkout завершается ошибкой (код 1), ветка не переключается, но функция возвращает `True`. | Проверять код возврата Git: при `code != 0` возвращать `False` (`Fail-Closed`). | При ошибке git checkout `abort_hypo` возвращает `False`. | FIXED-VERIFIED |
| AUD-FITE-024 | HIGH | CONFIRMED_DEFECT | `Fite.md`: строка 262 (`TurnGuard.chk_diff`) и `core/turn_guard.py`: 12-20 | Блокировка многошаговых планов: `get_active(plan_txt)` выполняет `re.search` и всегда захватывает самый первый `* **Target File:**`, принадлежащий завершенному Шагу 1. Все последующие шаги блокируются навсегда. Кроме того, при `plan_txt=None` падает `TypeError`. | `get_active` должен определять целевой файл именно активного шага, а `chk_diff` обязан валидировать тип `plan_txt`. | Для плана из 2 шагов, где Шаг 1 завершен, а Шаг 2 активен, `chk_diff` разрешает изменение целевого файла Шага 2. | FIXED-VERIFIED |
| AUD-FITE-025 | MEDIUM | CONFIRMED_DEFECT | `Fite.md`: строки 121-122 (`RunbookGen.update_spec`), 315-316 (`RegressGuard.save_manifest`) | Неатомарная прямая перезапись файлов: прямой `open(path, "w")` немедленно усекает файл до 0 байт. При сбое процесса спека или манифест безвозвратно теряются. | Применять атомарную замену (`Path.with_suffix('.tmp')` -> `dump` -> `replace`). | Ошибка сериализации не должна разрушать существующий файл на диске. | FIXED-VERIFIED |
| AUD-FITE-026 | MEDIUM | CONFIRMED_DEFECT | `Fite.md`: строки 339-340, 358-360 (`BranchGuard._run_git`) | Необработанный `TypeError` при нестроковых элементах в `args`: передача `[None]` вызывает `TypeError` в `subprocess.run`, который не перехватывается блоком `except (TimeoutExpired, OSError)`. | Валидировать элементы списка `all(isinstance(x, str) for x in args)` или перехватывать `TypeError`. | `BranchGuard._run_git(["status", None])` возвращает `(1, "Invalid args")` без необработанного исключения. | FIXED-VERIFIED |
| AUD-FITE-027 | MEDIUM | CONFIRMED_DEFECT | `Fite.md`: строки 80-86 (`DefenseGuard.chk_protected`) | Ложные блокировки прикладных модулей: проверка `p in cls.PROTECTED_ROOTS` проверяет каждую часть пути. Файлы вида `src/app/rules/evaluator.py` блокируются как защищенные корни. | Сопоставлять `PROTECTED_ROOTS` только с корневым сегментом нормализованного относительного пути. | `chk_protected("src/app/schemas/user.py")` возвращает `(True, "OK")`. | FIXED-VERIFIED |
| AUD-FITE-028 | LOW | CONFIRMED_DEFECT | `Fite.md`: строки 42-43 (`is_valid_token`) | Необработанный `AttributeError` при нестроковом `expected_plan`: при `expected_plan=123` вызов `expected_plan.strip()` падает. | Проверять `if expected_plan is not None: if not isinstance(expected_plan, str): return False`. | `is_valid_token("APPROVE PLAN-1", expected_plan=123)` возвращает `False`. | FIXED-VERIFIED |
| AUD-FITE-029 | MEDIUM | CONFIRMED_DEFECT | `core/semantic_memory.py`: строки 63-64 (`SemanticMemory.get_tmpl`) | Необработанный `ValueError` при выходе из песочницы: `self._get_path(cat, key)` вызывается до блока `try...except`. Попытка чтения `mem.get_tmpl("../escape", "k")` роняет метод. | Обернуть `_get_path` в `try...except (ValueError, OSError, TypeError): return None`. | `mem.get_tmpl("../outside", "key")` возвращает `None` (`Fail-Closed`). | FIXED-VERIFIED |
| AUD-FITE-030 | HIGH | CONFIRMED_DEFECT | `Fite.md`: Раздел 3 (`TestSecurityHardeningRound2`) | Отсутствие тестов в тестовом оракуле (Validation Theater): исправления для AUD-FITE-021, 022, 028, 029 заявлены как верифицированные, но в `TestSecurityHardeningRound2` отсутствуют проверяющие методы для них. | Добавить в `TestSecurityHardeningRound2` тесты: `test_abort_hypo_non_string_reason`, `test_abort_hypo_id_collision_hash`, `test_is_valid_token_invalid_type`, `test_semantic_memory_escape_fail_closed`. | Тестовый оракул запускает и валидирует все новые дефекты (100% assertions pass). | FIXED-VERIFIED |
| AUD-FITE-031 | MEDIUM | CONFIRMED_DEFECT | `Fite.md`: Раздел 5 (Чек-лист) | Рассинхронизация чек-листа: указано `Все 20 дефектов устранены`, хотя дефектов уже 29 (и теперь 36). | Актуализировать счетчик и чек-лист до полного перечня устраненных дефектов. | Текст чек-листа отражает актуальное число дефектов и их статусы. | FIXED-VERIFIED |
| AUD-FITE-032 | CRITICAL | CONFIRMED_DEFECT | `Fite.md`: строка 296 (`TurnGuard.get_active`) | Ложное усечение секции `## Active Step`: вызов `parts.split("##", 1)[0]` разбивает строку по любому `##`, включая заголовки уровней `###`, `####` (например, `### Next Actions` или `### Sub-step`), из-за чего блок активного шага обрезается до пустой строки или теряет `Target File`. | Использовать безопасное разделение только по заголовкам уровня 2: `re.split(r"(?m)^##\s+", parts, maxsplit=1)[0]` или эквивалентный срез. | Разметка с подзаголовками `### Sub-heading` внутри `## Active Step` корректно парсится и возвращает `Target File`. | FIXED-VERIFIED |
| AUD-FITE-033 | HIGH | CONFIRMED_DEFECT | `Fite.md`: строка 293 (`TurnGuard.get_active`) | Регистрозависимость маркера активного шага: поиск `## Active Step` через `txt.split("## Active Step", 1)` чувствителен к регистру (например, `## ACTIVE STEP` или `## active step` не обнаруживается). | Использовать регистронезависимый поиск `re.search(r"(?im)^##\s+active\s+step\b", txt)`. | `TurnGuard.get_active` корректно извлекает секцию независимо от регистра символов в заголовке. | FIXED-VERIFIED |
| AUD-FITE-034 | MEDIUM | CONFIRMED_DEFECT | `Fite.md`: строки 223-228 (`BranchGuard.abort_hypo`) | Коллизия ID гипотезы при повторном сбое с другой причиной: хеш `hashlib.sha256(clean_name.encode()).hexdigest()[:4]` вычисляется только от `clean_name`, а не от `reason` или времени/счетчика. Повторная попытка с тем же именем гипотезы отбрасывается. | Включить в расчет хеша `reason` или дифференцирующий счетчик/соль для уникальности записи сбоя. | Повторные сбои гипотезы с тем же именем, но разными причинами сохраняются в L2-памяти без потерь. | FIXED-VERIFIED |
| AUD-FITE-035 | MEDIUM | CONFIRMED_DEFECT | `Fite.md`: строка 243 (`BranchGuard.abort_hypo`) | Игнорирование кода возврата при удалении scratch-ветки Git: вызов `cls._run_git(["branch", "-D", bname])` не проверяет код возврата. При ошибке удаления ветки (например, блокировка или права) статус ошибки теряется. | Проверять код возврата и возвращать `False` или фиксировать ошибку при сбое удаления ветки (`Fail-Closed`). | Сбой команды удаления ветки фиксируется или обрабатывается без маскировки. | FIXED-VERIFIED |
| AUD-FITE-036 | LOW | CONFIRMED_DEFECT | `Fite.md`: строка 224 (`BranchGuard.abort_hypo`) | Загрязнение множества `existing_ids` значениями `None`: `set(f.get("id") for f in records)` при наличии записей без поля `id` добавляет `None` в множество. | Использовать фильтрацию `set(f.get("id") for f in records if isinstance(f.get("id"), str))`. | Поврежденные записи без ключа `id` не засоряют множество идентификаторов. | FIXED-VERIFIED |
| AUD-FITE-037 | HIGH | CONFIRMED_DEFECT | `Fite.md`: строка 113 (`RunbookGen.update_spec`) | Необработанный `TypeError` при `spec_p=None`: вызов `os.path.isfile(spec_p)` до блока `try...except` выбрасывает исключение при нестроковом пути, нарушая протокол Fail-Closed. | Добавить валидацию `isinstance(spec_p, (str, Path))` или перенести проверку внутрь защищенного блока `try...except`. | `RunbookGen().update_spec(None, approve_token="APPROVE P")` возвращает `False` без падения. | FIXED-VERIFIED |
| AUD-FITE-038 | CRITICAL | CONFIRMED_DEFECT | `core/defense_guard.py`: строки 47-54, 71-77, 161-167 (`chk_syntax`, `chk_ident`, `chk_danger`, `get_defs`) | Необработанный `TypeError` при `code=None`: методы оборачивают `ast.parse` только в `except SyntaxError:`. Передача `code=None` вызывает `TypeError`, аварийно останавливая выполнение методов защиты Tier 0. | Валидировать тип аргумента `if not isinstance(code, str): return False, "Invalid code type"` либо перехватывать `(SyntaxError, TypeError)`. | `DefenseGuard.chk_syntax(None)` и `DefenseGuard.chk_danger(None)` возвращают `(False, "...")` без выброса исключений. | FIXED-VERIFIED |
| AUD-FITE-039 | HIGH | CONFIRMED_DEFECT | `Fite.md`: строки 94-96 (`DefenseGuard.chk_protected`) | Ложная блокировка тестов журналирования в `tests/logs/`: проверка `any(p in cls.IMMUTABLE_LOGS for p in norm_parts)` проверяет все сегменты пути. Тестовый файл `tests/logs/test_logger.py` блокируется навсегда даже при `allow_test_edit=True` и валидном токене. | Проверять неизменяемость логов строго по корню пути (`norm_parts[0] == "logs"`) либо по имени файла (`norm_parts[-1] == "guard_audit.jsonl"`). | `chk_protected("tests/logs/test_logger.py", allow_test_edit=True, approve_token="APPROVE P")` возвращает `(True, "OK")`. | FIXED-VERIFIED |
| AUD-FITE-040 | HIGH | CONFIRMED_DEFECT | `core/artifact_guard.py`: строки 10-16, 29-37 и `core/regression_guard.py` (`chk_manifest`) | Искажение хеша 0-байтовых файлов и сокрытие удаления в `chk_manifest`: `verify_file` с `min_sz=1` возвращает пустую строку `""` вместо канонического SHA-256 (`e3b0c44...`). Удаление 0-байтового файла с диска не фиксируется проверкой `chk_manifest` из-за совпадения `"" == ""`. | Установить `min_sz=0` при вычислении хешей файлов, генерировать честный SHA-256 пустого файла и проверять существование файла в `chk_manifest`. | 0-байтовый файл хешируется в `e3b0c44...`; удаление пустого файла из манифеста детектируется как дрифт. | FIXED-VERIFIED |
| AUD-FITE-041 | MEDIUM | CONFIRMED_DEFECT | `core/defense_guard.py`: строки 96-108 (`DefenseGuard.chk_path`) | Необработанный `TypeError` при `path_str=None` или `root_str=None`: `chk_path` перехватывает только `(ValueError, RuntimeError)`. Вызов `Path(None)` роняет метод. | Расширить перехват исключений до `(ValueError, RuntimeError, TypeError)`. | `DefenseGuard.chk_path(None, "root")` возвращает `(False, "Invalid path: ...")`. | FIXED-VERIFIED |
| AUD-FITE-042 | MEDIUM | CONFIRMED_DEFECT | `core/runbook_gen.py`: строки 77-80 (`RunbookGen.gen_spec`) | Неатомарная запись спецификации: прямой `open(out_p, "w")` без временного файла `.tmp` и `replace` создает риск повреждения спеки сборки при сбое процесса. | Реализовать транзакционную запись через временный файл `.tmp` и атомарную замену `os.replace`. | Ошибка в процессе записи `gen_spec` не оставляет разрушенный файл в целевой директории. | FIXED-VERIFIED |
| AUD-FITE-043 | HIGH | CONFIRMED_DEFECT | `fite/fite_round3.md`: Решение 1 (`FloodGuard`) | Обход сетевых фильтров через PowerShell `-enc` (Base64), `FromBase64String`, обфускацию кавычками/бэктиками и сетевые алиасы (`irm`, `iwr`, `certutil`). | Внедрить нормализацию команды со снятием кавычек/бэктиков и регулярные выражения для Base64/алиасов. | `FloodGuard.chk_cmd("powershell -enc ...")` и `irm` блокируются со статусом `BANNED_ENCODED_COMMAND` / `BANNED_NETWORK_TOOL`. | FIXED-VERIFIED |
| AUD-FITE-044 | CRITICAL | CONFIRMED_DEFECT | `fite/fite_round3.md`: Решение 2 (`FtsMemory`) | FTS5 Syntax Injection Crash: поисковые запросы со спецсимволами `*`, `AND`, `NOT`, `OR`, `c++`, `[ERROR]`, `error: connection reset` роняют SQLite по `OperationalError` (unterminated string, no such column) и скрытно возвращают пустые результаты. | Санитизировать поисковые запросы через извлечение термов `[\w]+` и экранирование в `"{term}"`. | Запросы со спецсимволами и двоеточиями успешно и безопасно находят совпадения без исключений. | FIXED-VERIFIED |
| AUD-FITE-045 | CRITICAL | CONFIRMED_DEFECT | `fite/fite_round3.md`: Решение 2 (`FtsMemory`) | Утечка дескрипторов соединений SQLite на Windows: использование `with sqlite3.connect(...) as conn` управляет только транзакцией и НЕ закрывает соединение, вызывая `[WinError 32] PermissionError` при удалении или перезапуске БД. | Реализовать методы `close()`, `__enter__` и `__exit__` с принудительным закрытием дескрипторов. | БД разблокируется после выхода из контекста; тесты удаления файла в `tearDown` проходят без ошибок. | FIXED-VERIFIED |
| AUD-FITE-046 | HIGH | CONFIRMED_DEFECT | `fite/fite_round3.md`: Решение 2 (`FtsMemory`) | Блокировка базы данных при конкурирующем доступе нескольких агентов в Windows (`OperationalError: database is locked`). | Включить режим `PRAGMA journal_mode = WAL;`, `timeout=10.0` и `PRAGMA busy_timeout = 5000;`. | Конкурирующие писатели и читатели успешно обслуживаются очередью блокировок без ошибок. | FIXED-VERIFIED |
| AUD-FITE-047 | MEDIUM | CONFIRMED_DEFECT | `fite/fite_round3.md`: Решение 1 (`FloodGuard`) | Неконтролируемый сброс содержимого файлов в консоль: прямые вызовы `cat <file>`, `type <file>` и `Get-Content` без флагов пагинации/ограничения строк заливают окно контекста. | Запретить `cat`/`type` без конвейера пагинации и требовать явные флаги `-TotalCount`/`-First`/`-Last` для `Get-Content`. | Неограниченные дампы файлов блокируются со статусом `UNCONSTRAINED_FILE_DUMP` / `UNCONSTRAINED_GET_CONTENT`. | FIXED-VERIFIED |
| AUD-FITE-048 | CRITICAL | CONFIRMED_DEFECT | `fite/fite_round3.md`: Решение 4 (`render_checkpoint_yaml`) | YAML Injection через f-строки: передача переносов строк `\n`, кавычек и спецсимволов YAML в `run_id` или путях артефактов ломает синтаксис чекпоинта (`yaml.parser.ParserError`). | Сериализовать строковые поля и пути строго через `json.dumps()` в валидном формате JSON/YAML. | Имена файлов с двоеточиями, переносами строк и кавычками корректно парсятся `yaml.safe_load`. | FIXED-VERIFIED |
| AUD-FITE-049 | HIGH | CONFIRMED_DEFECT | `fite/fite_round3.md`: Решение 4 (`render_checkpoint_yaml`) | Падение генератора чекпоинта по `PermissionError: [Errno 13]` при попытке чтения файла, занятого другим процессом (`SharingViolation` на Windows). | Обернуть чтение и хеширование в `try...except (PermissionError, OSError)`. | Заблокированный файл пропускается с фиксацией ошибки без аварийного падения всего чекпоинта. | FIXED-VERIFIED |
| AUD-FITE-050 | HIGH | CONFIRMED_DEFECT | `fite/fite_round3.md`: Решение 4 (`render_checkpoint_yaml`) | Directory Traversal и Sandbox Escape: передача относительных путей `../../` позволяла хешировать файлы вне корня рабочего пространства. | Нормализовать пути через `Path.resolve()` и валидировать нахождение внутри корня репозитория. | Попытки выхода за пределы рабочей директории безопасно отклоняются. | FIXED-VERIFIED |
| AUD-FITE-051 | HIGH | CONFIRMED_DEFECT | `fite/fite_round3.md`: Решение 3 (`build_subagent_spec`) | Anti-Downgrade Bypass: критик/аудитор запускается на слабой модели `flash` при дефолтном `is_adversary=False`, нарушая принцип асимметрии интеллекта. | Автоматически определять роль аудитора по ключевым словам (`auditor`, `critic`, `red_team`, `verifier`) и принудительно выставлять `Model: 'pro'`. | Попытка запуска аудитора на `flash` игнорируется в пользу `pro` (`Anti-Downgrade Invariant`). | FIXED-VERIFIED |
| AUD-FITE-052 | MEDIUM | CONFIRMED_DEFECT | `fite/fite_round3.md`: Решение 3 (`clean_worktree`) | Сбой очистки изолированного worktree на Windows из-за скрытых файлов `.git` с атрибутом Read-Only (`PermissionError [WinError 5]`). | Добавить обработчик снятия прав `os.chmod(p, stat.S_IWRITE)` и 3 попытки с задержкой при блокировках. | Временные каталоги изолированных веток безопасно и полностью удаляются. | FIXED-VERIFIED |
| AUD-FITE-053 | HIGH | CONFIRMED_DEFECT | `fite/fite_round3.md`: Решение 4 (`write_checkpoint_atomic`) | Неатомарная запись чекпоинта: прямой сброс в файл отчета при обрыве питания или аварийной остановке оставляет полузаписанный разрушенный файл. | Применять транзакционную запись в `.tmp` файл с `flush()`, `os.fsync()` и атомарной заменой `os.replace`. | Прерывание записи не разрушает существующий валидный чекпоинт на диске. | FIXED-VERIFIED |
| AUD-FITE-054 | CRITICAL | CONFIRMED_DEFECT | `fite/fite_round4.md`: `core/pre_tool_guard.py` | Windows cp1251 decode failure: `sys.stdin` на Windows запускается в cp1251, вызывая `UnicodeDecodeError` при чтении UTF-8 путей с кириллицей (`Эталон ИИ`). | Принудительно реконфигурировать поток `sys.stdin.reconfigure(encoding='utf-8', errors='replace')`. | Кириллические пути успешно парсятся без исключений кодировки. | FIXED-VERIFIED |
| AUD-FITE-055 | HIGH | CONFIRMED_DEFECT | `fite/fite_round4.md`: `core/pre_tool_guard.py` | Засорение stdout: сторонние warnings библиотек ломают JSON-парсер Antigravity (`JSONDecodeError`). | Отключить предупреждения `warnings.simplefilter('ignore')` и строго изолировать stdout. | На stdout выводится исключительно один валидный JSON вердикта. | FIXED-VERIFIED |
| AUD-FITE-056 | CRITICAL | CONFIRMED_DEFECT | `fite/fite_round4.md`: `core/pre_tool_guard.py` | Fail-Open при пустом вводе stdin: при пустом stdin или обрыве потока хук возвращал `{"decision": "allow"}`. | Возвращать строго `{"decision": "deny", "reason": "EMPTY_STDIN"}` при пустом вводе. | Пустой ввод приводит к гарантированному отказу (Fail-Closed). | FIXED-VERIFIED |
| AUD-FITE-057 | HIGH | CONFIRMED_DEFECT | `fite/fite_round4.md`: `core/pre_tool_guard.py` | Обход через `run_command`: прямая запись файлов в шелл-командах (powershell редиректы, `python -c open(...)`). | Интегрировать проверку `DefenseGuard.chk_cmd()` в обработчик инструмента `run_command`. | Попытки деструктивной записи через терминал блокируются с `CMD_VIOLATION`. | FIXED-VERIFIED |
| AUD-FITE-058 | CRITICAL | CONFIRMED_DEFECT | `fite/fite_round4.md`: `core/pre_tool_guard.py` | Path Traversal и подстрочный обход: проверка через `ap in clean` разрешала редактирование любого `.py` файла и обход `../../`. | Нормализовать пути через `Path.resolve()` и сопоставлять строго через `target.is_relative_to(ap)`. | Обходы путей и подстрок надежно блокируются с `RO_LOCK`. | FIXED-VERIFIED |
| AUD-FITE-059 | CRITICAL | CONFIRMED_DEFECT | `fite/fite_round4.md`: `core/pre_tool_guard.py` | Инвертированная логика `chk_protected`: незащищенный код ошибочно разрешался без утвержденного плана. | Все файлы по умолчанию заблокированы (Gate 1 RO-Lock); доступ разрешен строго при совпадении с активным шагом. | Редактирование любого кода без утвержденного плана блокируется. | FIXED-VERIFIED |

### Граф состояний замечания:
```
           ┌──────────────┐
           │     OPEN     │
           └──────┬───────┘
                  │
        ┌─────────┴─────────┐
        ▼                   ▼
┌──────────────┐    ┌─────────────────────────┐
│   PARTIAL    │    │  REJECTED-WITH-EVIDENCE │
└──────┬───────┘    └─────────────────────────┘
       │
       ▼
┌──────────────────┐
│  FIXED-VERIFIED  │
└──────────────────┘
```

- `OPEN` — дефект подтвержден контрпримером, ожидает реакции Автора;
- `PARTIAL` — Автор внес правку, но контрпример всё ещё воспроизводится либо устранение неполное;
- `REJECTED-WITH-EVIDENCE` — Автор предоставил математическое, логическое или фактическое опровержение критики; Оппонент подтвердил корректность отклонения;
- `FIXED-VERIFIED` — правка внесена Автором, Оппонент лично провел повторную верификацию (`PASS`), и регрессий не обнаружено;
- `CONFLICT-STOP` — обнаружена рассинхронизация артефактов, несогласованная одновременная запись или нарушение границ полномочий.

---

## 5. Аудит регрессий (Regression Verification)

При каждом исправлении дефекта Оппонент обязан:
1. Повторно выполнить сценарий первичного контрпримера (убедиться, что падение устранено);
2. Запустить контрольный набор базовых проверок (убедиться, что исправление не сломало ранее работавшие сценарии);
3. Проверить границы измененного фрагмента на предмет побочных эффектов (`Side-Effects`).

---

## 6. Протокол разрешения споров и эскалации

1. Если Автор и Оппонент не приходят к согласию по замечанию после **2 итераций аргументации**:
   - Оппонент фиксирует позицию сторон в секции `Нерешенные разногласия (Unresolved Disputes)`;
   - Обе стороны формируют минимальный пакет эскалации (краткая суть, цитата исходного контракта, контрпример, аргумент защиты);
   - Вызывается внешний арбитр (пользователь или независимый консилиум).
2. Запрещено бесконечно зацикливать спор («пинг-понг аргументами» без новых проверяемых фактов).

---

## 7. Чек-лист финальной приемки Оппонента

Перед подтверждением завершения задачи Оппонент проверяет:
- [x] Все замечания находятся в терминальных статусах (`FIXED-VERIFIED` или `REJECTED-WITH-EVIDENCE`);
- [x] Нет ни одного замечания в статусе `OPEN` или `PARTIAL`;
- [x] Проведены проверки на граничные условия, переполнения, гонки и типы;
- [x] Выполнен регрессионный прогон;
- [x] Зафиксированы остаточные риски и технические ограничения среды.
