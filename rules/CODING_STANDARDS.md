---
name: coding-standards
description: Canonical Engineering and Code Quality Standard
applyTo: "core/**/*.py,tests/**/*.py"
excludeAgent: ["cad_critic"]
---

# CODING_STANDARDS.md — Canonical Engineering & Code Quality Standard

> **Status:** Mandatory normative standard for generation, refactoring, and auditing stages (Tier 0 / Gate 2 / Gate 5).
> **Scope:** Activated strictly for paths matching `applyTo` glob pattern (CLAIM-0011).
> **Invariant:** Zero dead code, zero placeholders, 100% strict static typing, deterministic proof of work.

---

## 1. Mutation Budgets & Atomic Changes (Diff & Mutation Budgets)

* **Diff Budget Limit:** Diff per DAG step <= 30 actual lines; for decomposed atomic subplans <= 15 lines. Changes exceeding limits MUST be split via subplan fission.
* **Scope Isolation (`allowed_paths`):** Each atomic step touches strictly 1 target file explicitly declared in `allowed_paths`. Touching foreign files triggers `SCOPE_VIOLATION` -> immediate rollback.
* **Prohibition of Opportunistic Refactoring (No Side-Fixes):** Unrelated bugs discovered during work are logged to backlog/handoff, never fixed in the active step diff.
* **Prohibition of Complete Module Rewrites (Strangler Fig):** Overwriting functional modules from scratch is prohibited. Apply Strangler Fig pattern for incremental replacement.

---

## 2. Static and AST Architecture Limits (AST Constraints)

* **Function/Method Length:** Maximum **40 lines** of logical code. Exceeding functions must be split into private helpers (`_helper_func`).
* **Cyclomatic Complexity:** Maximum **7** independent execution paths per function/method. Deeply nested `if/elif/else` and multiple ternaries are prohibited.
* **Nesting Depth:** Maximum **3 levels** of block nesting (loops, conditions, contexts). Use Guard Clauses and Early Returns.
* **Prohibition of Dynamic Execution:** `eval()`, `exec()`, dynamic `__import__`, and untrusted `pickle.loads` are strictly prohibited.

---

## 3. Static Typing & Data Contracts (Typing & Interfaces)

* **100% Type Coverage:** All function signatures, arguments, and return types must declare explicit static type annotations.
* **No Blind Types:**
  * Python: Unsubstantiated `Any` is prohibited. Use `Union`, `Optional`, `Generic`, or `TypeVar`.
  * TypeScript: `any` is prohibited (use `unknown` with explicit type narrowing).
* **Data Models over Raw Dictionaries:** Internal DTOs, configs, and inter-module messages must use typed structures (`@dataclass(frozen=True)` or `pydantic.BaseModel`). Raw `dict[str, Any]` for business entities is prohibited.
* **Immutability by Default:** Data objects and enums are immutable unless mutable state is architecturally required.

---

## 4. Naming Conventions & File Structures

* **Identifier Length Limits (Universal Slug & Name Rule):**
  * Utility files, branches, and decision keys <= 20 chars (except `test_*.py`).
  * Variables, functions, methods, and classes in generated code <= 15 chars.
* **Python Conventions:**
  * Modules/Packages: `snake_case`, concise nouns (`guard.py`, `router.py`).
  * Classes: `PascalCase` (`Critic`, `Router`).
  * Functions/Methods: `snake_case`, verb forms (`verify`, `pack`).
  * Constants: `UPPER_SNAKE_CASE` (`MAX_DIFF = 30`).
  * Private members: single leading underscore (`_helper`).
* **No Duplicate Names:** Parallel files with suffixes `_v2`, `_new`, `_temp`, `_copy` are prohibited.

---

## 5. Defensive Programming & Error Handling

* **Fail-Closed Principle:** Ambiguity, malformed inputs, or authorization errors trigger immediate failure (`raise SpecificError` / return `FAIL`). Degraded execution with invalid state is prohibited.
* **No Blind Error Suppression:**
  * `except: pass` and `except Exception: pass` are strictly prohibited.
  * Catch only specific targeted exceptions (`FileNotFoundError`, `ValueError`, `KeyError`).
  * Caught exceptions must be logged or wrapped in domain exceptions (`from err`).
* **Path & Link Liveness:** File operations must use `pathlib.Path.resolve()` with `allowed_roots` validation. All referenced paths and links must physically exist on disk (`Path.exists()`).

---

## 6. Testing & Anti-Fake Invariants

* **No Fake Mocks:** Mocks reproducing self-tested logic tautologically are prohibited. Integration tests must verify real files, real AST trees, and real schemas.
* **Determinism:** Tests must be deterministic and independent of network or non-seeded randomness (`seed=42`).
* **Acceptance Criteria (Strict Exit Code):** Verification is valid ONLY with raw terminal output displaying `exit_code: 0` and passed test suites. Subjective claims without console logs are void.
* **Active Tactile Verification (ITV):** Every artifact or code unit must undergo 4 independent physical probes before completion:
  1. `File Probe`: file exists, `size > 0` for `__init__.py`, `size >= 100` bytes for functional code modules.
  2. `AST Probe`: passes deterministic parser (`ast.parse`) with strict limits (lines <= 40, complexity <= 7, names <= 15).
  3. `Execution Poke`: invoked with boundary inputs (`edge cases`) verifying strict output contracts.
  4. `Subprocess Probe`: clean isolated invocation via `python -c "..."` with `exit_code: 0`.
* **Explicit Metric Protocol (No Validation Theater):** Any metric (coverage, memory, integrity) that fails to compute MUST be returned as explicit `null`/`None`. Hardcoding fake defaults (e.g. `0.0`, `100%`) is prohibited. By Gate 10 (Fail-Closed), a critical metric returning `null` triggers an immediate `BLOCK`.

---

## 7. Read-After-Write Protocol (RAW Checklist)

After invoking `write_to_file` or `replace_file_content`, the agent must:
1. Inspect modified lines via `view_file`.
2. Verify absence of duplicated methods and cut-off code blocks.
3. Validate imports (all called entities imported, zero cyclic imports).
4. Verify absence of hardcoded secrets, API keys, or machine-specific absolute paths.

---

## 8. Token Economy & Sandbox Derive Rule (Gate 8 Enforcement)

* **Do not dump — derive:** Reading or dumping raw files or logs into the chat context (> 100 lines) is strictly prohibited. The agent must execute a single-purpose local Python or shell script to extract the exact AST node, count, regex match, or slice, returning only the derived value.
* **Prohibition of Direct Network Dumping:** Direct invocation of network download commands (`curl`, `wget`, `Invoke-WebRequest`, `irm`, `certutil`) in `run_command` is strictly blocked.
* **Bounded Output Invariant:** Terminal commands producing unbounded directory walks (`Get-ChildItem -Recurse`, `dir /s`, `find .`) or raw file streams (`cat <file>`, `type <file>`) must be constrained with pagination flags (`-TotalCount`, `| head -n 30`).

