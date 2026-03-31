"""FirstToKnow agents — powered by Google ADK + LiteLLM.

Structure:
    agent.py              → FirstToKnowAgent class (subclasses LlmAgent)
    _tools.py             → FirstToKnowTools class (get_tools() → list[FunctionTool])
    instructions/         → Instruction constants (system prompts)
"""

from firsttoknow.agents.agent import FirstToKnowAgent, run_agent

__all__ = ["FirstToKnowAgent", "run_agent"]
