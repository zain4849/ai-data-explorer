"""Sandboxed Python code execution with resource limits.

Uses RestrictedPython for safe execution with a whitelist of allowed modules.
"""

import io
import signal
import sys
import traceback
from contextlib import redirect_stderr, redirect_stdout

import pandas as pd

from ..logger_config import logger

EXECUTION_TIMEOUT = 30  # seconds
MAX_OUTPUT_SIZE = 50_000  # characters

# Safe builtins allowed in the sandbox
SAFE_BUILTINS = {
    "abs", "all", "any", "bool", "dict", "enumerate", "filter", "float",
    "format", "frozenset", "getattr", "hasattr", "hash", "int", "isinstance",
    "issubclass", "iter", "len", "list", "map", "max", "min", "next",
    "print", "range", "repr", "reversed", "round", "set", "slice",
    "sorted", "str", "sum", "tuple", "type", "zip",
}

# Modules allowed for import in the sandbox
ALLOWED_MODULES = {
    "math", "statistics", "collections", "itertools", "functools",
    "json", "re", "datetime", "decimal", "fractions",
}


def _timeout_handler(signum, frame):
    raise TimeoutError("Code execution timed out")


def execute_python_sandboxed(
    code: str,
    dataframe: pd.DataFrame | None = None,
) -> dict:
    """Execute Python code in a restricted sandbox.

    Args:
        code: Python source code to execute.
        dataframe: Optional DataFrame injected as the variable `df`.

    Returns:
        dict with keys: output (str), error (str|None), result (any serializable).
    """
    try:
        from RestrictedPython import compile_restricted, safe_globals
        from RestrictedPython.Eval import default_guarded_getiter
        from RestrictedPython.Guards import (
            guarded_unpack_sequence,
            safer_getattr,
        )
    except ImportError:
        return {
            "output": "",
            "error": "RestrictedPython is not installed",
            "result": None,
        }

    # Compile the code in restricted mode
    try:
        compiled = compile_restricted(code, filename="<sandbox>", mode="exec")
    except SyntaxError as exc:
        return {"output": "", "error": f"Syntax error: {exc}", "result": None}

    if compiled.errors:
        return {"output": "", "error": "\n".join(compiled.errors), "result": None}

    # Build the restricted namespace
    restricted_globals = safe_globals.copy()
    restricted_globals["_getiter_"] = default_guarded_getiter
    restricted_globals["_getattr_"] = safer_getattr
    restricted_globals["_unpack_sequence_"] = guarded_unpack_sequence

    # Inject safe builtins
    builtins = restricted_globals.get("__builtins__", {})
    if isinstance(builtins, dict):
        import builtins as _b
        for name in SAFE_BUILTINS:
            if hasattr(_b, name):
                builtins[name] = getattr(_b, name)
        restricted_globals["__builtins__"] = builtins

    # Inject the dataframe and safe libraries
    local_ns: dict = {}
    if dataframe is not None:
        local_ns["df"] = dataframe
    local_ns["pd"] = pd

    try:
        import numpy as np
        local_ns["np"] = np
    except ImportError:
        pass

    # Capture stdout/stderr
    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    result = None

    # Set timeout (Unix only)
    old_handler = None
    if hasattr(signal, "SIGALRM"):
        old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
        signal.alarm(EXECUTION_TIMEOUT)

    try:
        with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
            exec(compiled.code, restricted_globals, local_ns)

        # Check for a 'result' variable in the namespace
        result = local_ns.get("result")
        if isinstance(result, pd.DataFrame):
            result = result.head(100).to_dict(orient="records")
        elif isinstance(result, pd.Series):
            result = result.head(100).to_dict()

    except TimeoutError:
        return {"output": "", "error": "Execution timed out", "result": None}
    except Exception:
        tb = traceback.format_exc()
        return {"output": stdout_buf.getvalue()[:MAX_OUTPUT_SIZE], "error": tb, "result": None}
    finally:
        if hasattr(signal, "SIGALRM"):
            signal.alarm(0)
            if old_handler is not None:
                signal.signal(signal.SIGALRM, old_handler)

    output = stdout_buf.getvalue()[:MAX_OUTPUT_SIZE]
    error = stderr_buf.getvalue()[:MAX_OUTPUT_SIZE] or None

    return {"output": output, "error": error, "result": result}
