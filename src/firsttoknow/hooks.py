"""Pre-commit hook entry point for FirstToKnow Guard.

Why a separate module instead of reusing cli.py?
────────────────────────────────────────────────
pre-commit runs hooks as standalone executables. It needs a simple
function that:
1. Runs the guard check
2. Prints the report
3. Returns an exit code (0 = pass, 1 = fail)

The Typer CLI adds overhead (argument parsing, help text, error
handling) that isn't needed when pre-commit is doing the calling.
This module is the thinnest possible wrapper around run_guard().

This is the same pattern that ruff, mypy, and black use —
a console_scripts entry point that pre-commit can invoke directly.
"""

from __future__ import annotations

import sys
from pathlib import Path

from firsttoknow.guard import run_guard
from firsttoknow.renderer import render_guard_report


def main() -> int:
    """Run the guard and return an exit code.

    Why return an int instead of calling sys.exit() directly?
    ─────────────────────────────────────────────────────────
    Returning the code makes this function testable — tests can
    check the return value without catching SystemExit exceptions.
    We only call sys.exit() in the if __name__ block.

    Returns:
        0 if all checks pass, 1 if critical issues found.
    """
    # pre-commit sets CWD to the repo root, so Path(".") is correct.
    # .resolve() converts it to an absolute path for safety.
    path = Path().resolve()

    try:
        report = run_guard(path)
    except Exception as exc:
        # Don't crash silently — show what went wrong
        print(f"FirstToKnow Guard error: {exc}", file=sys.stderr)  # noqa: T201
        return 1

    render_guard_report(report)

    return 0 if report.passed else 1


if __name__ == "__main__":
    sys.exit(main())
