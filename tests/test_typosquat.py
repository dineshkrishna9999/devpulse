"""Tests for the typosquatting detection module.

Testing strategy:
─────────────────
Pure unit tests — no mocks, no network, no filesystem.
These are CPU-only string comparison tests that run in <10ms total.

We test each detection layer independently, then the public API.
"""

from __future__ import annotations

from firsttoknow.models import Severity
from firsttoknow.typosquat import (
    _find_typosquat_matches,
    _is_one_edit_away,
    _is_transposition,
    _normalize_for_comparison,
    _strip_affixes,
    check_typosquat,
)

# ──────────────────────────────────────────────
# Normalization tests
# ──────────────────────────────────────────────


class TestNormalization:
    """Test PEP 503 normalization + npm scope stripping."""

    def test_lowercase(self) -> None:
        assert _normalize_for_comparison("Flask") == "flask"

    def test_underscore_to_hyphen(self) -> None:
        assert _normalize_for_comparison("typing_extensions") == "typing-extensions"

    def test_dot_to_hyphen(self) -> None:
        assert _normalize_for_comparison("socket.io") == "socket-io"

    def test_consecutive_separators(self) -> None:
        assert _normalize_for_comparison("foo__bar") == "foo-bar"

    def test_npm_scope_stripped(self) -> None:
        assert _normalize_for_comparison("@babel/core") == "core"

    def test_no_scope_unchanged(self) -> None:
        assert _normalize_for_comparison("express") == "express"


# ──────────────────────────────────────────────
# Transposition detection tests
# ──────────────────────────────────────────────


class TestTransposition:
    """Test adjacent character swap detection."""

    def test_adjacent_swap(self) -> None:
        """reqeusts vs requests — classic typosquat."""
        assert _is_transposition("reqeusts", "requests") is True

    def test_identical_strings(self) -> None:
        assert _is_transposition("requests", "requests") is False

    def test_different_lengths(self) -> None:
        assert _is_transposition("req", "requ") is False

    def test_two_non_adjacent_diffs(self) -> None:
        """Two differences but not adjacent — not a transposition."""
        assert _is_transposition("abcd", "xbcz") is False

    def test_swap_at_start(self) -> None:
        assert _is_transposition("lfask", "flask") is True

    def test_swap_in_middle(self) -> None:
        assert _is_transposition("djnago", "django") is True


# ──────────────────────────────────────────────
# One-edit-away tests
# ──────────────────────────────────────────────


class TestOneEditAway:
    """Test single character insertion/deletion detection."""

    def test_one_char_deleted(self) -> None:
        """requets vs requests — missing one 's'."""
        assert _is_one_edit_away("requets", "requests") is True

    def test_one_char_inserted(self) -> None:
        """requestss vs requests — extra 's'."""
        assert _is_one_edit_away("requestss", "requests") is True

    def test_identical(self) -> None:
        assert _is_one_edit_away("flask", "flask") is False

    def test_two_chars_different(self) -> None:
        assert _is_one_edit_away("reques", "requests") is False  # 2 chars shorter

    def test_char_deleted_from_end(self) -> None:
        """nump vs numpy — missing 'y' at end."""
        assert _is_one_edit_away("nump", "numpy") is True

    def test_char_inserted_in_middle(self) -> None:
        assert _is_one_edit_away("flassk", "flask") is True


# ──────────────────────────────────────────────
# Prefix/suffix stripping tests
# ──────────────────────────────────────────────


class TestStripAffixes:
    """Test common typosquatting prefix/suffix removal."""

    def test_python_prefix(self) -> None:
        assert _strip_affixes("python-requests") == "requests"

    def test_py_prefix(self) -> None:
        assert _strip_affixes("py-flask") == "flask"

    def test_python_suffix(self) -> None:
        assert _strip_affixes("requests-python") == "requests"

    def test_no_affixes(self) -> None:
        assert _strip_affixes("requests") == "requests"

    def test_js_prefix(self) -> None:
        assert _strip_affixes("js-lodash") == "lodash"

    def test_lib_suffix(self) -> None:
        assert _strip_affixes("express-lib") == "express"

    def test_does_not_strip_to_empty(self) -> None:
        """Should not strip if it would leave nothing meaningful."""
        # "py-" is len 3, "py-" starts with "py-" but result would be ""
        # Guard: len(name) > len(prefix)
        assert _strip_affixes("py-") == "py-"


# ──────────────────────────────────────────────
# Full match detection tests
# ──────────────────────────────────────────────


class TestFindTyposquatMatches:
    """Test the multi-layer detection pipeline."""

    def test_exact_match_not_flagged(self) -> None:
        """Installing the REAL 'requests' should not be flagged."""
        matches = _find_typosquat_matches("requests")
        assert matches == []

    def test_exact_match_with_normalization(self) -> None:
        """'Requests' (capitalized) normalizes to 'requests' — not a typosquat."""
        matches = _find_typosquat_matches("Requests")
        assert matches == []

    def test_underscore_variant_not_flagged(self) -> None:
        """'typing_extensions' normalizes to 'typing-extensions' — exact match."""
        matches = _find_typosquat_matches("typing_extensions")
        assert matches == []

    def test_transposition_caught(self) -> None:
        """'reqeusts' should be flagged as similar to 'requests'."""
        matches = _find_typosquat_matches("reqeusts")
        assert len(matches) >= 1
        assert any(popular == "requests" for popular, _ in matches)

    def test_missing_char_caught(self) -> None:
        """'requets' should be flagged."""
        matches = _find_typosquat_matches("requets")
        assert len(matches) >= 1
        assert any(popular == "requests" for popular, _ in matches)

    def test_extra_char_caught(self) -> None:
        """'requestss' should be flagged."""
        matches = _find_typosquat_matches("requestss")
        assert len(matches) >= 1
        assert any(popular == "requests" for popular, _ in matches)

    def test_prefix_trick_caught(self) -> None:
        """'python-requests' should be flagged (wraps the real name)."""
        matches = _find_typosquat_matches("python-requests")
        assert len(matches) >= 1
        assert any(popular == "requests" for popular, _ in matches)

    def test_suffix_trick_caught(self) -> None:
        """'flask-python' should be flagged."""
        matches = _find_typosquat_matches("flask-python")
        assert len(matches) >= 1
        assert any(popular == "flask" for popular, _ in matches)

    def test_completely_different_name_not_flagged(self) -> None:
        """'mycompany-internal-utils' shouldn't match anything."""
        matches = _find_typosquat_matches("mycompany-internal-utils")
        assert matches == []

    def test_numpy_transposition(self) -> None:
        """'nmupy' (transposition) should flag against 'numpy'."""
        matches = _find_typosquat_matches("nmupy")
        assert len(matches) >= 1
        assert any(popular == "numpy" for popular, _ in matches)

    def test_django_transposition(self) -> None:
        """'djnago' should flag against 'django'."""
        matches = _find_typosquat_matches("djnago")
        assert len(matches) >= 1
        assert any(popular == "django" for popular, _ in matches)


# ──────────────────────────────────────────────
# Public API tests (check_typosquat → GuardFinding)
# ──────────────────────────────────────────────


class TestCheckTyposquat:
    """Test the public API that guard.run_guard() calls."""

    def test_returns_warning_severity(self) -> None:
        """Typosquat findings should be WARNING, not CRITICAL."""
        findings = check_typosquat("reqeusts")
        assert len(findings) >= 1
        assert all(f.severity == Severity.WARNING for f in findings)

    def test_finding_mentions_popular_package(self) -> None:
        """The finding should tell the user WHICH real package it resembles."""
        findings = check_typosquat("reqeusts")
        assert any("requests" in f.title for f in findings)

    def test_finding_includes_dep_name(self) -> None:
        """The finding should include the suspicious dep name."""
        findings = check_typosquat("reqeusts")
        assert all(f.package == "reqeusts" for f in findings)

    def test_clean_dep_returns_empty(self) -> None:
        """A completely unrelated name returns no findings."""
        findings = check_typosquat("my-unique-package-name-12345")
        assert findings == []

    def test_real_package_returns_empty(self) -> None:
        """The real 'requests' package should NOT be flagged."""
        findings = check_typosquat("requests")
        assert findings == []

    def test_ecosystem_passed_through(self) -> None:
        """The ecosystem should be passed through to the finding."""
        findings = check_typosquat("expresss", ecosystem="npm")
        assert all(f.ecosystem == "npm" for f in findings)

    def test_python_prefix_warning(self) -> None:
        """'python-django' should produce a warning."""
        findings = check_typosquat("python-django")
        assert len(findings) >= 1
        assert any("django" in f.title for f in findings)


# ──────────────────────────────────────────────
# Edge case tests
# ──────────────────────────────────────────────


class TestEdgeCases:
    """Make sure nothing crashes on weird inputs."""

    def test_empty_string(self) -> None:
        findings = check_typosquat("")
        assert isinstance(findings, list)

    def test_very_long_name(self) -> None:
        findings = check_typosquat("a" * 500)
        assert isinstance(findings, list)

    def test_special_characters_normalized(self) -> None:
        """Names with dots/underscores should normalize correctly."""
        findings = check_typosquat("requests")  # exact match
        assert findings == []

    def test_npm_scoped_exact_match(self) -> None:
        """@evil/requests → normalizes to 'requests' → exact match → not flagged."""
        findings = check_typosquat("@evil/requests")
        assert findings == []
