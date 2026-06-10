# Path Safety — Safe Destination Validation

Use the following pattern to validate file destinations before writing.
This prevents path-traversal attacks and ensures output lands in an expected directory.

## Reference Implementation

```python
import os

SAFE_BASES = [
    "D:\\",
    os.path.expanduser("~/Documents/Obsidian Vault/Hermes/"),
]

def safe_path(dest: str) -> bool:
    \"\"\"
    Return True if *dest* resolves to a path under one of the SAFE_BASES.
    Rejects paths containing '..', '~' (after expansion), '%', or environment
    variable references that fall outside the allowlist.
    \"\"\"
    abs_dest = os.path.abspath(dest)
    return any(abs_dest.startswith(os.path.abspath(base)) for base in SAFE_BASES)
```

## Rules

1. **Always call `safe_path(dest)` before opening any file for writing.**
2. Reject input containing `..`, `~` (unexpanded), `%` unless handled safely.
3. Keep `SAFE_BASES` in a single, auditable location (e.g., environment variables
   or this module).
4. Log or raise a `SecurityError` when `safe_path()` returns `False`.
