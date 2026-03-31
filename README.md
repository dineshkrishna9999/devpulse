# 🔔 LastToKnow

### Because being the last to know isn't a personality trait — it's a fixable problem.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## The Problem

You've been here:

- 😤 LiteLLM shipped a **breaking change** — you found out when your prod pipeline crashed
- 🤦 Google ADK released the exact fix you needed — **2 weeks ago**
- 😶 A repo with **15K stars** solves your exact problem — you never heard of it
- 🫠 Your colleague casually drops *"oh yeah, that was deprecated last month"*

You're not lazy. You're not out of touch. **There's just too much happening and no one tool that watches YOUR stack.**

Dependabot bumps versions but doesn't explain why it matters. daily.dev shows generic news, not YOUR news. GitHub Watch drowns you in noise.

## The Fix

**LastToKnow** is an AI agent that knows your stack, tracks what matters to YOU, and briefs you like a personal tech analyst.

```bash
# 30 seconds to set up
lasttoknow scan                          # Auto-detects deps from your project
lasttoknow track --topic "AI agents"     # Add topics you care about
lasttoknow brief --model gpt-4o          # Get your personalized briefing
```

```
╭───────────────────────── 🔔 LastToKnow Briefing ──────────────────────────╮
│                                                                            │
│  🔴 CRITICAL — action needed                                              │
│  ├── litellm 1.41.0 → Breaking: Azure auth flow changed                   │
│  └── google-adk 1.28.0 → New: Multi-agent orchestration                   │
│                                                                            │
│  🟡 WORTH KNOWING                                                         │
│  ├── 🔥 Trending: "hermes-agent" (15K ⭐ this week)                        │
│  └── HN: "AI agent memory" discussion (342 points)                        │
│                                                                            │
│  🟢 FYI                                                                   │
│  ├── pytest 9.0.2 — minor bugfixes                                        │
│  └── 3 new repos matching "AI agents" trending today                      │
│                                                                            │
╰──────────────────────────────── model: gpt-4o ─────────────────────────────╯
```

**No dashboards.** No browser tabs. No newsletters you'll never read. Just one command and you're the **first** to know.

## Why LastToKnow > Everything Else

| Tool | What it does | What it doesn't do |
|------|-------------|-------------------|
| **Dependabot** | Bumps versions | Doesn't explain what changed or why it matters to YOU |
| **daily.dev** | Generic news feed | Not personalized to your stack |
| **GitHub Watch** | Notifications | Drowns you in noise, zero intelligence |
| **Newsletters** | Curated by someone else | Not YOUR stack, stale by the time you read |
| **🔔 LastToKnow** | **Knows YOUR stack, fetches real-time data, AI synthesizes and prioritizes** | — |

## Get Started in 60 Seconds

```bash
# Install
git clone https://github.com/dineshkrishna9999/lasttoknow.git
cd lasttoknow && uv sync

# Point it at any LLM (Azure, OpenAI, Gemini, Claude, Ollama)
echo "OPENAI_API_KEY=sk-..." > .env
uv run lasttoknow config model gpt-4o

# Tell it what you care about
uv run lasttoknow track litellm                  # PyPI package
uv run lasttoknow track --github BerriAI/litellm # GitHub repo
uv run lasttoknow track --topic "AI agents"      # Broad topic
uv run lasttoknow scan                           # Or just auto-detect everything

# Get briefed
uv run lasttoknow brief
```

That's it. You're no longer the last to know.

## All Commands

```bash
# Track / Untrack
lasttoknow track <name>                 # Track a PyPI package
lasttoknow track --github owner/repo    # Track a GitHub repo
lasttoknow track --topic "AI agents"    # Track a topic
lasttoknow track litellm --version 1.40 # Track with current version
lasttoknow scan                         # Auto-detect from pyproject.toml
lasttoknow untrack <name>               # Stop tracking

# Briefings
lasttoknow brief                        # Get your AI briefing
lasttoknow brief --model azure/gpt-4.1  # Use a specific model
lasttoknow brief --raw                  # Raw text, no formatting

# Manage
lasttoknow list                         # See what you're tracking
lasttoknow status                       # Full overview
lasttoknow config model <model>         # Set default LLM
lasttoknow config show                  # Show settings
```

## Works With Any LLM

Powered by [LiteLLM](https://github.com/BerriAI/litellm) — so you're not locked in:

| Provider | Model | Env Var |
|----------|-------|---------|
| **Azure OpenAI** | `azure/gpt-4.1` | `AZURE_API_KEY` |
| **OpenAI** | `gpt-4o` | `OPENAI_API_KEY` |
| **Google Gemini** | `gemini/gemini-2.0-flash` | `GEMINI_API_KEY` |
| **Anthropic Claude** | `anthropic/claude-sonnet-4-20250514` | `ANTHROPIC_API_KEY` |
| **Ollama (free!)** | `ollama/llama3` | None needed |

## How It Works Under the Hood

```
You run: lasttoknow brief
              │
              ▼
   ┌─────────────────────┐
   │   LastToKnow CLI    │  Reads your tracked items from ~/.lasttoknow/
   └──────────┬──────────┘
              │
              ▼
   ┌─────────────────────┐
   │    ADK Agent +      │  AI decides which tools to call based on
   │    LiteLLM          │  what you're tracking
   └──────────┬──────────┘
              │
     ┌────────┼────────┐
     ▼        ▼        ▼
  ┌──────┐ ┌──────┐ ┌──────┐
  │ PyPI │ │GitHub│ │  HN  │   Real API calls — not hallucinated data
  │  API │ │  API │ │ API  │
  └──────┘ └──────┘ └──────┘
              │
              ▼
   ┌─────────────────────┐
   │  AI synthesizes     │  Prioritizes: 🔴 Critical → 🟡 Important → 🟢 FYI
   │  and prioritizes    │  Thinks like a senior dev briefing a CTO
   └──────────┬──────────┘
              │
              ▼
   ┌─────────────────────┐
   │  Rich terminal      │  Beautiful panels, tables, colored output
   │  output             │
   └─────────────────────┘
```

The AI **decides** which tools to call — you don't hardcode the flow. You just say "brief me" and it figures out what to check.

## Development

```bash
git clone https://github.com/dineshkrishna9999/lasttoknow.git
cd lasttoknow && uv sync

uv run poe check        # Run ALL checks (format, lint, typecheck, test)
uv run poe test         # Just tests
uv run poe fmt          # Format code
```

### Project Structure

```
src/lasttoknow/
├── cli.py              # CLI commands (Typer)
├── config.py           # Config & persistence (~/.lasttoknow/)
├── models.py           # Data models
├── renderer.py         # Rich terminal output
├── scanner.py          # Dependency scanner
└── agents/
    ├── agent.py        # ADK agent + runner
    ├── _tools.py       # API fetchers (PyPI, GitHub, HN)
    └── instructions/
        └── briefing.py # System prompt
```

## License

[MIT](LICENSE) — do whatever you want with it.

---

<p align="center">
  <b>Stop being the last to know.</b><br>
  <a href="https://github.com/dineshkrishna9999/lasttoknow">⭐ Star this repo</a> if you've ever found out about a breaking change from a colleague.
</p>
