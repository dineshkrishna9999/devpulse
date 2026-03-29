# 📡 DevPulse

> Your AI-powered tech radar. Track packages, releases, trends — and get briefed like a CTO.

[![CI](https://github.com/dineshkrishna9999/devpulse/actions/workflows/ci.yml/badge.svg)](https://github.com/dineshkrishna9999/devpulse/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

**You're always the last to know.**

LiteLLM shipped a breaking change — you found out from a colleague. Google ADK released the exact fix you needed — 2 weeks ago. A repo with 15K stars solves your exact problem — you never heard of it.

**DevPulse fixes this.** It's an AI agent that knows YOUR stack, tracks what matters, and briefs you like a personal tech analyst.

## How It Works

```bash
# Tell it what you care about
devpulse track google-adk
devpulse track litellm
devpulse track "AI agents"

# Or auto-detect from your project
devpulse scan

# Get your personalized briefing
devpulse brief
```

```
📡 DEVPULSE BRIEFING — Mar 29, 2026

🔴 CRITICAL
├── litellm 1.41.0 → Breaking: Azure auth flow changed
│   "If you use Azure OpenAI, update your AZURE_API_VERSION..."
└── google-adk 1.28.0 → New: Multi-agent orchestration
    "New AgentTeam class lets agents collaborate on tasks..."

🟡 WORTH KNOWING
├── 🔥 Trending: "hermes-agent" (15K ⭐ this week)
│   Relevant: uses same ADK pattern as your code
├── Claude Code shipped hooks + background agents
└── HN: "AI agent memory" discussion (342 points)

🟢 FYI
├── pytest 9.0.2 — minor bugfixes
├── ruff 0.15.0 — new rules for Python 3.13
└── 3 new repos matching "AI agents" trending today
```

## Features

- **Track anything** — PyPI packages, GitHub repos, topics, products
- **Auto-detect dependencies** — scans `pyproject.toml`, `package.json`, `requirements.txt`
- **AI-powered briefings** — powered by Google ADK + LiteLLM (any LLM works)
- **Smart prioritization** — 🔴 Critical / 🟡 Important / 🟢 FYI
- **Works with any LLM** — Azure OpenAI, OpenAI, Gemini, Claude, Ollama (local)
- **Works without AI too** — `--no-ai` mode shows raw data, no API key needed
- **Beautiful terminal output** — powered by Rich

## Installation

```bash
pip install devpulse
# or
uv add devpulse
```

## Quick Start

```bash
# 1. Configure your LLM (optional — works without it too)
cp .env.example .env
# Edit .env with your API key

# 2. Track your stack
devpulse scan                      # Auto-detect from project files
devpulse track litellm             # Track a PyPI package
devpulse track --github owner/repo # Track a GitHub repo
devpulse track "AI agents"         # Track a topic

# 3. Get briefed
devpulse brief                     # AI-powered briefing
devpulse brief --no-ai             # Raw data, no AI
devpulse brief --json              # JSON output
devpulse brief --markdown          # Markdown (for notes/blog)

# 4. Deep dive
devpulse explain litellm 1.41.0    # What changed & why it matters
devpulse trending                  # Trending repos & news
devpulse content-ideas             # Blog/LinkedIn content ideas
```

## Supported LLM Providers

DevPulse uses [LiteLLM](https://github.com/BerriAI/litellm) under the hood, so **any LLM works**:

| Provider | Model Example | Env Var |
|----------|---------------|---------|
| Azure OpenAI | `azure/gpt-4.1` | `AZURE_API_KEY` |
| OpenAI | `gpt-4o` | `OPENAI_API_KEY` |
| Google Gemini | `gemini/gemini-2.0-flash` | `GEMINI_API_KEY` |
| Anthropic Claude | `anthropic/claude-sonnet-4-20250514` | `ANTHROPIC_API_KEY` |
| Ollama (local) | `ollama/llama3` | None needed! |

```bash
devpulse brief --model azure/gpt-4.1
devpulse brief --model ollama/llama3
```

## Data Sources

DevPulse aggregates from multiple sources:

- **PyPI** — package releases, changelogs, breaking changes
- **GitHub** — repo releases, trending repositories
- **Hacker News** — top stories, relevant discussions
- **Reddit** — posts from r/programming, r/Python, r/MachineLearning, etc.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    DevPulse CLI                      │
│              (click + rich terminal)                 │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│           ADK Orchestrator Agent                     │
│         (Google ADK + LiteLLM)                       │
│                                                      │
│  Tools: fetch_releases, search_trending,             │
│         generate_briefing, explain_release,           │
│         suggest_content_ideas                         │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│              Data Sources (httpx)                     │
│  PyPI API · GitHub API · HN Algolia · Reddit JSON    │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│              Local State (~/.config/devpulse/)        │
│  tracked.json · briefings/ · cache/                  │
└─────────────────────────────────────────────────────┘
```

## Development

```bash
# Clone & install
git clone https://github.com/dineshkrishna9999/devpulse.git
cd devpulse
uv sync

# Run checks
uv run poe fmt          # Format code
uv run poe lint         # Lint code
uv run poe typecheck    # Type check (mypy)
uv run poe test         # Run tests
uv run poe check        # Run ALL checks

# Run the CLI
uv run devpulse status
```

### Project Structure

```
src/devpulse/
├── cli.py              # CLI entry point (click)
├── config.py           # Config & tracked items management
├── models.py           # Data models (dataclasses)
├── renderer.py         # Rich terminal output
├── utils.py            # Shared utilities
├── sources/            # Data source fetchers
│   ├── pypi.py         # PyPI releases
│   ├── github.py       # GitHub releases + trending
│   ├── hackernews.py   # Hacker News
│   ├── reddit.py       # Reddit posts
│   ├── changelog.py    # Changelog parser
│   └── deps.py         # Local dependency scanner
└── agents/             # Google ADK agents
    └── orchestrator.py # AI orchestrator
```

## Contributing

Contributions are welcome! Please open an issue first to discuss what you'd like to change.

## License

[MIT](LICENSE)
