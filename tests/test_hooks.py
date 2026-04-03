"""Tests for the pre-commit hook integration.

Tests cover two things:
1. hooks.main() — the entry point pre-commit calls directly
2. guard --init — the CLI command that installs the hook

Testing strategy:
────────────────
- hooks.main() is tested by mocking run_guard (same as test_guard.py)
- guard --init is tested with a real tmp_path directory containing
  a fake .pre-commit-config.yaml, using CliRunner (same as test_cli.py)
- We do NOT call pre-commit install in tests (that would need a real
  git repo with pre-commit installed). We mock subprocess.run instead.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from firsttoknow.cli import app
from firsttoknow.hooks import main
from firsttoknow.models import GuardFinding, GuardReport, Severity

if TYPE_CHECKING:
    from pathlib import Path

runner = CliRunner()


# ──────────────────────────────────────────────
# hooks.main() tests
# ──────────────────────────────────────────────


class TestHooksMain:
    """Test the pre-commit entry point function."""

    @patch("firsttoknow.hooks.run_guard")
    @patch("firsttoknow.hooks.render_guard_report")
    def test_returns_zero_when_clean(self, mock_render: MagicMock, mock_guard: MagicMock) -> None:
        """No critical findings → exit code 0 (push allowed)."""
        mock_guard.return_value = GuardReport(
            findings=[
                GuardFinding(package="flask", ecosystem="pypi", severity=Severity.INFO, title="clean"),
            ]
        )
        assert main() == 0
        mock_render.assert_called_once()

    @patch("firsttoknow.hooks.run_guard")
    @patch("firsttoknow.hooks.render_guard_report")
    def test_returns_one_when_critical(self, mock_render: MagicMock, mock_guard: MagicMock) -> None:
        """Critical finding → exit code 1 (push blocked)."""
        mock_guard.return_value = GuardReport(
            findings=[
                GuardFinding(
                    package="bad-pkg",
                    ecosystem="pypi",
                    severity=Severity.CRITICAL,
                    title="CVE found",
                ),
            ]
        )
        assert main() == 1
        mock_render.assert_called_once()

    @patch("firsttoknow.hooks.run_guard")
    def test_returns_one_on_exception(self, mock_guard: MagicMock) -> None:
        """If run_guard crashes, return 1 (fail safe — don't silently let bad code through)."""
        mock_guard.side_effect = RuntimeError("git not found")
        assert main() == 1

    @patch("firsttoknow.hooks.run_guard")
    @patch("firsttoknow.hooks.render_guard_report")
    def test_returns_zero_when_no_new_deps(self, mock_render: MagicMock, mock_guard: MagicMock) -> None:
        """No new dependencies → info finding, pass."""
        mock_guard.return_value = GuardReport(
            findings=[
                GuardFinding(
                    package="dependencies",
                    ecosystem="—",
                    severity=Severity.INFO,
                    title="No new dependencies detected",
                ),
            ]
        )
        assert main() == 0


# ──────────────────────────────────────────────
# guard --init tests
# ──────────────────────────────────────────────


class TestGuardInit:
    """Test the guard --init CLI command."""

    def test_init_no_config_file(self, tmp_path: Path) -> None:
        """If no .pre-commit-config.yaml exists, warn and exit 1."""
        result = runner.invoke(app, ["guard", "--init", str(tmp_path)])
        assert result.exit_code == 1
        assert "No .pre-commit-config.yaml found" in result.output

    @patch("firsttoknow.cli.subprocess.run")
    def test_init_adds_hook_to_config(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Should append the guard hook config to .pre-commit-config.yaml."""
        # Create a minimal pre-commit config
        config_file = tmp_path / ".pre-commit-config.yaml"
        config_file.write_text(
            "repos:\n  - repo: https://github.com/pre-commit/pre-commit-hooks\n    rev: v5.0.0\n    hooks:\n      - id: check-ast\n"
        )

        # Mock pre-commit install succeeding
        mock_run.return_value = MagicMock(returncode=0, stderr="")

        result = runner.invoke(app, ["guard", "--init", str(tmp_path)])
        assert result.exit_code == 0
        assert "Added guard hook" in result.output

        # Verify the config was updated
        updated_config = config_file.read_text()
        assert "firsttoknow-guard" in updated_config
        assert "pre-push" in updated_config
        assert "language: system" in updated_config

    @patch("firsttoknow.cli.subprocess.run")
    def test_init_idempotent(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Running --init twice should not duplicate the hook config.

        Idempotency matters because users will forget they already ran it.
        The command should say 'already configured' not add a second copy.
        """
        config_file = tmp_path / ".pre-commit-config.yaml"
        config_file.write_text("repos:\n  - repo: local\n    hooks:\n      - id: firsttoknow-guard\n")

        mock_run.return_value = MagicMock(returncode=0, stderr="")

        result = runner.invoke(app, ["guard", "--init", str(tmp_path)])
        assert result.exit_code == 0
        assert "already configured" in result.output

        # Config should NOT have been modified (no duplicate)
        updated = config_file.read_text()
        assert updated.count("firsttoknow-guard") == 1

    @patch("firsttoknow.cli.subprocess.run")
    def test_init_pre_commit_not_installed(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """If pre-commit binary isn't found, warn but don't crash."""
        config_file = tmp_path / ".pre-commit-config.yaml"
        config_file.write_text("repos: []\n")

        mock_run.side_effect = FileNotFoundError("pre-commit not found")

        result = runner.invoke(app, ["guard", "--init", str(tmp_path)])
        assert result.exit_code == 0  # still succeeds (config was written)
        assert "pre-commit not found" in result.output

    @patch("firsttoknow.cli.subprocess.run")
    def test_init_installs_pre_push_hook(self, mock_run: MagicMock, tmp_path: Path) -> None:
        """Should call pre-commit install --hook-type pre-push."""
        config_file = tmp_path / ".pre-commit-config.yaml"
        config_file.write_text("repos: []\n")

        mock_run.return_value = MagicMock(returncode=0, stderr="")

        runner.invoke(app, ["guard", "--init", str(tmp_path)])

        # Verify pre-commit was called with the right args
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "pre-commit" in call_args
        assert "install" in call_args
        assert "--hook-type" in call_args
        assert "pre-push" in call_args
