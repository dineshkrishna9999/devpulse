# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.3.0] - 2026-03-31

### Changed

- **Renamed project from LastToKnow to FirstToKnow** — aspirational > self-deprecating
- Renamed all imports, CLI commands, config dir (`~/.firsttoknow/`), env var (`FIRSTTOKNOW_MODEL`)
- Agent now produces real summaries (2-3 sentences per item) instead of just headlines
- Every item includes a `[Read more]` link for optional deep-dive

## [0.2.0] - 2026-03-31

### Added

- Dev.to tool: fetch popular articles by tag (`fetch_devto_articles`)
- Reddit tool: fetch hot posts from any subreddit (`fetch_reddit_posts`)
- Agent now uses 5 data sources (PyPI, GitHub, Hacker News, Dev.to, Reddit)
- Structured briefing output with sections: 📦 Package Updates, 🔥 Trending Repos, 📰 News & Discussions, 💡 TL;DR
- 8 new tests for Dev.to and Reddit tools (89 total)

### Changed

- Rewrote agent instructions for structured, sectioned output
- Agent now calls at least 3 different tools per briefing
- README commands now include `uv run` prefix

## [0.1.0] - 2026-03-31

### Added

- CLI with Typer: `track`, `untrack`, `list`, `brief`, `scan`, `status`, `config`
- ADK agent with LiteLLM backbone for AI-powered briefings
- 3 tool functions: PyPI releases, GitHub trending, Hacker News top stories
- Dependency scanner: auto-detect from `pyproject.toml` / `requirements.txt`
- Rich terminal output: panels, tables, colored text
- Config management with JSON persistence (`~/.firsttoknow/`)
- `.env` support via python-dotenv for API keys
- Works with any LLM provider: Azure OpenAI, OpenAI, Gemini, Claude, Ollama
- System prompt with priority levels: 🔴 Critical / 🟡 Important / 🟢 FYI
- 81 tests with full coverage across CLI, agents, config, scanner, and models
