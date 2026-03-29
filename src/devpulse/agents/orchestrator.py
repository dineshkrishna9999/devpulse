"""DevPulse orchestrator agent — the core AI brain.

This is where the magic happens. The orchestrator is a Google ADK agent
that uses LiteLLM for model routing, so it works with any LLM provider:
Azure, OpenAI, Gemini, Claude, Ollama, etc.

How it works:
1. We define a system prompt that tells the agent HOW to think
2. We give it tools (from tools.py) that let it FETCH real data
3. The agent decides which tools to call, in what order
4. It synthesizes the results into a prioritized briefing

The ADK pattern is simple:
    Agent(model, instruction, tools) → Runner → events → response
"""

from __future__ import annotations

import logging

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from devpulse.agents.tools import (
    fetch_github_trending,
    fetch_hackernews_top,
    fetch_pypi_releases,
)

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# System prompt — this shapes how the agent thinks
# ──────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are DevPulse, a personal tech analyst for developers.

When the user asks for a briefing, you should:
1. Use fetch_pypi_releases to check each tracked package for updates
2. Use fetch_github_trending to find interesting new repos
3. Use fetch_hackernews_top to find relevant discussions

Then synthesize everything into a prioritized briefing:
- 🔴 CRITICAL: Breaking changes, security issues in tracked packages
- 🟡 IMPORTANT: New features, major updates, highly relevant trending repos
- 🟢 FYI: Minor updates, interesting discussions, loosely related trends

Rules:
- Be specific — mention version numbers, star counts, dates
- Be concise — 1-2 sentences per item
- Think like a senior dev briefing a CTO
"""


# ──────────────────────────────────────────────
# Agent creation
# ──────────────────────────────────────────────


def create_agent(model: str) -> Agent:
    """Create the DevPulse ADK agent.

    Args:
        model: LiteLLM model string — any provider works.
               Examples: "azure/gpt-4.1", "gpt-4o", "gemini/gemini-2.0-flash",
               "anthropic/claude-sonnet-4-20250514", "ollama/llama3".
    """
    return Agent(
        name="devpulse",
        model=LiteLlm(model=model),
        instruction=SYSTEM_PROMPT,
        description="AI-powered tech radar that tracks packages, releases, and trends.",
        tools=[fetch_pypi_releases, fetch_github_trending, fetch_hackernews_top],
    )


# ──────────────────────────────────────────────
# Running the agent
# ──────────────────────────────────────────────


def run_agent(model: str, message: str) -> str:
    """Run the DevPulse agent with a user message and return the response.

    This is the main entry point. It:
    1. Creates the agent with the given model
    2. Sets up an in-memory session (no persistence needed between runs)
    3. Sends the message through the ADK Runner
    4. Collects and returns the final text response

    Args:
        model: LiteLLM model string (e.g. "azure/gpt-4.1").
        message: The user's message — e.g. "Brief me on litellm, google-adk".

    Returns:
        The agent's text response (the briefing).
    """
    agent = create_agent(model)

    # InMemorySessionService = no database, sessions live in memory.
    # Perfect for a CLI tool where each run is independent.
    session_service = InMemorySessionService()  # type: ignore[no-untyped-call]

    # The Runner ties everything together:
    # agent + session → processes messages → yields events
    runner = Runner(
        agent=agent,
        session_service=session_service,
        app_name="devpulse",
        auto_create_session=True,
    )

    # Build the user message in ADK's format
    content = types.Content(
        role="user",
        parts=[types.Part(text=message)],
    )

    # Run the agent and collect the response.
    # The runner yields events as the agent thinks, calls tools, and responds.
    # We grab the last text response — that's the final answer.
    response = ""
    for event in runner.run(new_message=content, session_id="session", user_id="user"):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    response = part.text

    return response
