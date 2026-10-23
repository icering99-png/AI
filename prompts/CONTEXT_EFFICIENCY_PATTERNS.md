# prompts/CONTEXT_EFFICIENCY_PATTERNS.md — Context Efficiency & Safe Derivation Patterns

> **Status:** Normative Guidance for Agents.  
> **Core Principle:** «Do not dump — derive». Avoid dumping raw files into the context window. Use deterministic, bounded AST one-liners or bounded file slices to extract exact answers.

---

## 1. Prohibited Anti-Patterns (Banned by FloodGuard)

The following commands flood the context window and trigger automatic rejection by `FloodGuard`:

| Anti-Pattern | Rejection Code | Reason |
| :--- | :--- | :--- |
| `cat <file>`, `type <file>` (without pipe) | `UNCONSTRAINED_FILE_DUMP` | Dumps entire file into stdout/context. |
| `Get-Content <file>`, `gc <file>` | `UNCONSTRAINED_GET_CONTENT` | Missing line limits; risks megabytes of tokens. |
| `Get-ChildItem -Recurse`, `dir /s`, `ls -r` | `UNCONSTRAINED_RECURSIVE_LISTING` | Unbounded recursive directory listing. |
| `powershell -enc <base64>`, `FromBase64String`| `BANNED_ENCODED_COMMAND` | Opaque encoded payload bypassing audits. |
| `curl`, `wget`, `iwr`, `irm`, `certutil` | `BANNED_NETWORK_TOOL` | Unauthorized external network I/O. |
| `urllib`, `requests`, `httpx`, `aiohttp` | `BANNED_NETWORK_API` | Direct Python network library usage. |

---

## 2. Recommended Safe Derivation Patterns

### 2.1. Python AST Inspection One-Liners (Derive, Do Not Dump)
Extract exact function names, classes, or docstrings without reading the entire source code into context:

```bash
# List all top-level functions in a module:
python -c "import ast; tree = ast.parse(open('core/runner.py', encoding='utf-8').read()); print([n.name for n in tree.body if isinstance(n, ast.FunctionDef)])"

# List all classes in a module:
python -c "import ast; tree = ast.parse(open('core/defense_guard.py', encoding='utf-8').read()); print([n.name for n in tree.body if isinstance(n, ast.ClassDef)])"

# Check maximum line length of functions in a file:
python -c "import ast; tree = ast.parse(open('core/crash_recovery.py', encoding='utf-8').read()); print([(n.name, n.end_lineno - n.lineno) for n in tree.body if isinstance(n, ast.FunctionDef)])"
```

### 2.2. Bounded PowerShell Slices
When inspecting log files or text, always specify line bounds:

```powershell
# Read first 30 lines:
Get-Content -Path "system.log" -TotalCount 30

# Read last 30 lines:
Get-Content -Path "system.log" -Tail 30

# Filter exact patterns without dumping:
Select-String -Path "core/*.py" -Pattern "class\s+"
```

### 2.3. Safe File Reading in Python
Read files in chunks to avoid high RAM usage and memory bloat:

```python
with open(filepath, "rb") as f:
    while chunk := f.read(65536):
        process_chunk(chunk)
```
