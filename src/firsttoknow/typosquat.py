"""Typosquatting detection for new dependencies.

What is typosquatting?
─────────────────────
Attackers publish packages with names like `reqeusts` (instead of
`requests`) hoping developers mistype during install. Once installed,
these packages can steal credentials, mine crypto, or backdoor your app.

Architecture decision: WHY a hardcoded list instead of querying PyPI?
─────────────────────────────────────────────────────────────────────
1. Speed: comparing against ~100 strings is instant (~0.2ms per dep).
   Querying PyPI's search API would add 500ms+ per dependency.
2. Offline: guard should work without internet. For vuln checks we NEED
   the network, but typosquat detection is pure CPU.
3. No false positive flood: PyPI has 500k+ packages. Fuzzy-matching
   against ALL of them would flag everything. A curated list of
   the top ~100 packages catches the attacks that matter.
4. No new dependencies: stdlib `difflib` is all we need.

Detection layers (run in order):
────────────────────────────────
0. Exact match after normalization → skip (it's the real package)
1. SequenceMatcher ratio ≥ 0.85 → similar name (e.g. flaask → flask)
2. Adjacent character swap → transposition (e.g. reqeusts → requests)
3. Single char insertion/deletion → one edit away (e.g. requets → requests)
4. Common prefix/suffix wrapping → python-requests → requests
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher

from firsttoknow.models import GuardFinding, Severity

# ──────────────────────────────────────────────
# Popular package names (sorted, ~50 PyPI + ~50 npm)
# ──────────────────────────────────────────────
#
# Why these packages? They're the most downloaded / most depended-upon
# on PyPI and npm — the #1 targets for typosquatting attacks.
#
# Source: pypistats.org (PyPI), npmjs.com/browse/depended (npm)
# Last updated: 2026-04
#
# Maintainer note: keep this list sorted and under 120 entries.
# Re-check yearly against download stats.

POPULAR_PYPI: list[str] = [
    "aiohttp",
    "attrs",
    "beautifulsoup4",
    "black",
    "boto3",
    "celery",
    "certifi",
    "cffi",
    "charset-normalizer",
    "click",
    "colorama",
    "cryptography",
    "django",
    "fastapi",
    "filelock",
    "flask",
    "grpcio",
    "gunicorn",
    "httpx",
    "idna",
    "jinja2",
    "markupsafe",
    "matplotlib",
    "mypy",
    "numpy",
    "packaging",
    "pandas",
    "pillow",
    "pip",
    "platformdirs",
    "pluggy",
    "psycopg2",
    "pyarrow",
    "pydantic",
    "pygments",
    "pyjwt",
    "pymongo",
    "pytest",
    "python-dateutil",
    "pytz",
    "pyyaml",
    "redis",
    "requests",
    "rich",
    "ruff",
    "scikit-learn",
    "scipy",
    "setuptools",
    "six",
    "sqlalchemy",
    "starlette",
    "tomli",
    "tqdm",
    "typing-extensions",
    "urllib3",
    "uvicorn",
    "virtualenv",
    "wheel",
]

POPULAR_NPM: list[str] = [
    "axios",
    "chalk",
    "commander",
    "cors",
    "debug",
    "dotenv",
    "ejs",
    "eslint",
    "express",
    "glob",
    "inquirer",
    "jest",
    "jsonwebtoken",
    "lodash",
    "minimist",
    "mkdirp",
    "moment",
    "mongoose",
    "morgan",
    "next",
    "nodemon",
    "passport",
    "postcss",
    "prettier",
    "prisma",
    "react",
    "react-dom",
    "react-router-dom",
    "redux",
    "rimraf",
    "semver",
    "sequelize",
    "socket.io",
    "tailwindcss",
    "tslib",
    "typescript",
    "uuid",
    "vite",
    "vue",
    "webpack",
    "ws",
    "yargs",
    "zod",
]


# ──────────────────────────────────────────────
# Normalization
# ──────────────────────────────────────────────


def _normalize_for_comparison(name: str) -> str:
    """Normalize a package name for typosquat comparison.

    Uses PEP 503 normalization (same approach as scanner._normalize):
    replace runs of [-_.] with a single hyphen, then lowercase.

    Also strips npm scopes (@scope/name → name) because scoped
    packages are a different namespace — @types/express is NOT
    a typosquat of express.
    """
    if "/" in name:
        name = name.split("/", 1)[1]
    return re.sub(r"[-_.]+", "-", name).lower()


# ──────────────────────────────────────────────
# Detection helpers
# ──────────────────────────────────────────────

# Prefix/suffix tricks used by typosquatters:
# "python-requests" wraps the real name with a prefix
# "flask-py" wraps the real name with a suffix
_COMMON_PREFIXES = ("python-", "py-", "node-", "js-")
_COMMON_SUFFIXES = ("-python", "-py", "-js", "-node", "-core", "-lib")

_SIMILARITY_THRESHOLD = 0.85
_MIN_NAME_LENGTH = 4


def _is_transposition(a: str, b: str) -> bool:
    """True if `a` and `b` differ by exactly one adjacent-character swap.

    Example: "reqeusts" vs "requests" — the 'u' and 'e' are swapped.
    This is the most common typo pattern when typing fast.
    """
    if len(a) != len(b):
        return False
    diffs = [i for i in range(len(a)) if a[i] != b[i]]
    return (
        len(diffs) == 2
        and diffs[1] == diffs[0] + 1
        and a[diffs[0]] == b[diffs[1]]
        and a[diffs[1]] == b[diffs[0]]
    )


def _is_one_edit_away(a: str, b: str) -> bool:
    """True if `a` and `b` differ by exactly one character insertion or deletion.

    Example: "requets" vs "requests" — one 's' is missing.
    We check by removing each character from the longer string and
    seeing if it matches the shorter one.
    """
    if abs(len(a) - len(b)) != 1:
        return False
    shorter, longer = (a, b) if len(a) < len(b) else (b, a)
    return any(longer[:i] + longer[i + 1 :] == shorter for i in range(len(longer)))


def _strip_affixes(name: str) -> str:
    """Strip common typosquatting prefixes and suffixes.

    Example: "python-requests" → "requests", "flask-py" → "flask"

    Won't strip if it would leave an empty string.
    """
    for prefix in _COMMON_PREFIXES:
        if name.startswith(prefix) and len(name) > len(prefix):
            name = name[len(prefix) :]
            break
    for suffix in _COMMON_SUFFIXES:
        if name.endswith(suffix) and len(name) > len(suffix):
            name = name[: -len(suffix)]
            break
    return name


# ──────────────────────────────────────────────
# Core detection
# ──────────────────────────────────────────────

# Build lookup structures at import time (once)
_ALL_POPULAR: set[str] = set()
_POPULAR_LIST: list[str] = []

for _name in POPULAR_PYPI + POPULAR_NPM:
    _norm = _normalize_for_comparison(_name)
    _ALL_POPULAR.add(_norm)
    _POPULAR_LIST.append(_norm)


def _find_typosquat_matches(dep_name: str) -> list[tuple[str, str]]:
    """Check if a dependency name looks like a typosquat of a popular package.

    Returns list of (popular_name, reason) tuples. Usually 0 or 1 match.
    """
    normalized = _normalize_for_comparison(dep_name)

    # Layer 0: exact match → it IS the popular package, skip
    if normalized in _ALL_POPULAR:
        return []

    matches: list[tuple[str, str]] = []

    for popular in _POPULAR_LIST:
        # Layer 1: SequenceMatcher similarity
        # Only for names ≥ 4 chars — short names produce too many false positives
        if len(normalized) >= _MIN_NAME_LENGTH and len(popular) >= _MIN_NAME_LENGTH:
            ratio = SequenceMatcher(None, normalized, popular).ratio()
            if ratio >= _SIMILARITY_THRESHOLD:
                matches.append((popular, f"very similar name (similarity: {ratio:.0%})"))
                continue  # don't double-flag same popular package

        # Layer 2: transposition (adjacent char swap)
        if _is_transposition(normalized, popular):
            matches.append((popular, "character swap (transposition)"))
            continue

        # Layer 3: single insertion or deletion
        if _is_one_edit_away(normalized, popular):
            matches.append((popular, "one character off (insertion/deletion)"))
            continue

        # Layer 4: prefix/suffix wrapping
        stripped = _strip_affixes(normalized)
        if stripped != normalized and stripped == popular:
            matches.append((popular, "wraps popular package with prefix/suffix"))

    return matches


# ──────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────


def check_typosquat(dep_name: str, ecosystem: str = "pypi") -> list[GuardFinding]:
    """Check if a dependency name is a potential typosquat.

    This is the public function called by guard.run_guard().

    Returns:
        List of GuardFinding(severity=WARNING) for each match.
        Empty list if the name looks clean.

    Why WARNING and not CRITICAL?
    ─────────────────────────────
    Typosquat detection is heuristic — it CAN produce false positives.
    A package named "my-requests-wrapper" might legitimately exist.
    WARNING alerts the developer without blocking the push.
    """
    matches = _find_typosquat_matches(dep_name)

    return [
        GuardFinding(
            package=dep_name,
            ecosystem=ecosystem,
            severity=Severity.WARNING,
            title=f"Possible typosquat of '{popular}'",
            details=(
                f"'{dep_name}' looks suspiciously similar to the popular package "
                f"'{popular}' — {reason}. Verify this is the package you intended."
            ),
        )
        for popular, reason in matches
    ]
