"""AI agents for DevPulse — powered by Google ADK + LiteLLM.

The agent architecture is simple:

    tools.py          → Functions the agent can call (fetch data from APIs)
    orchestrator.py   → The agent itself (system prompt + ADK setup + runner)

Usage:
    from devpulse.agents.orchestrator import run_agent

    response = run_agent(model="gpt-4o", message="Brief me on litellm")
"""

from devpulse.agents.orchestrator import create_agent, run_agent

__all__ = ["create_agent", "run_agent"]
