"""Chat service - integrates with agents from langchain_service"""
import sys
import os
from typing import Dict, List, Any, Iterator, Optional
import logging

# Robust: Füge sowohl backend-Root als auch Projekt-Root zum sys.path hinzu
_THIS_FILE = os.path.abspath(__file__)
_BACKEND_ROOT = os.path.abspath(os.path.join(_THIS_FILE, "../../../"))
_PROJECT_ROOT = os.path.abspath(os.path.join(_THIS_FILE, "../../../../"))
for _p in {_BACKEND_ROOT, _PROJECT_ROOT}:
    if _p not in sys.path:
        sys.path.append(_p)

from ..core.errors import UpstreamError, ValidationError
from ..core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def _ensure_gemini_env():
    """Ensure GOOGLE_API_KEY is present in process env for Gemini agent."""
    if settings.google_api_key and not os.getenv("GOOGLE_API_KEY"):
        os.environ["GOOGLE_API_KEY"] = settings.google_api_key
        logger.info("GOOGLE_API_KEY injected into environment for Gemini agent")


def run_agent(
    agent: str,
    messages: List[Dict[str, Any]],
    params: Optional[Dict[str, Any]] = None,
    stream: bool = False
) -> Dict[str, Any] | Iterator[Dict[str, Any]]:
    """
    Run an agent from langchain_service.

    This is the single integration point between the API and the agents.
    All agent logic and tool calls happen through the agents.

    Args:
        agent: Agent name ("qwen" or "gemini")
        messages: Conversation history (list of dicts with role/content)
        params: Additional parameters
        stream: Whether to stream the response

    Returns:
        Non-stream: Dict with {content, usage?, tool_calls?}
        Stream: Iterator yielding chunks as dicts
    """
    params = params or {}

    try:
        if agent == "qwen":
            return _run_qwen_agent(messages, params, stream)
        elif agent == "gemini":
            _ensure_gemini_env()
            return _run_gemini_agent(messages, params, stream)
        else:
            raise ValidationError(
                message=f"Unknown agent: {agent}",
                details={"available_agents": ["qwen", "gemini"]}
            )
    except ImportError as e:
        logger.error(f"Failed to import agent {agent}: {e}")
        raise UpstreamError(
            message=f"Agent {agent} not available",
            details={"error": str(e), "agent": agent}
        )
    except Exception as e:
        logger.error(f"Agent execution failed: {e}", exc_info=True)
        raise UpstreamError(
            message="Agent execution failed",
            details={"error": str(e), "agent": agent}
        )


def _run_qwen_agent(
    messages: List[Dict[str, Any]],
    params: Dict[str, Any],
    stream: bool
) -> Dict[str, Any] | Iterator[Dict[str, Any]]:
    """Run Qwen agent"""
    from langchain_service.qwen_agent_bgb import create_qwen_agent_bgb

    # Create agent
    enable_thinking = params.get("enable_thinking", True)
    agent = create_qwen_agent_bgb(enable_thinking=enable_thinking)

    # Extract user question from last user message
    user_question = None
    for msg in reversed(messages):
        if msg.get("role") == "user":
            user_question = msg.get("content")
            break

    if not user_question:
        raise ValidationError("No user message found in conversation history")

    # Extract thread_id from params if available
    thread_id = params.get("thread_id")

    # Prepare message history (all messages EXCEPT the last user message)
    message_history = [msg for msg in messages[:-1]] if len(messages) > 1 else None

    if stream:
        # Streaming not yet implemented in qwen_agent_bgb
        # For now, fall back to non-streaming
        return _run_qwen_non_stream(agent, user_question, message_history, thread_id)
    else:
        return _run_qwen_non_stream(agent, user_question, message_history, thread_id)


def _run_qwen_non_stream(agent, user_question: str, message_history: List[Dict[str, Any]] = None, thread_id: str = None) -> Dict[str, Any]:
    """Run Qwen agent without streaming"""
    result = agent.chat(user_question, message_history=message_history, thread_id=thread_id)

    # Extract tool calls from messages
    tool_calls = []
    for msg in result.get("messages", []):
        if fn_call := msg.get("function_call"):
            tool_calls.append({
                "name": fn_call.get("name"),
                "arguments": fn_call.get("arguments")
            })

    return {
        "content": result["final_response"],
        "usage": None,  # Qwen agent doesn't track usage yet
        "tool_calls": tool_calls if tool_calls else None
    }


def _run_gemini_agent(
    messages: List[Dict[str, Any]],
    params: Dict[str, Any],
    stream: bool
) -> Dict[str, Any] | Iterator[Dict[str, Any]]:
    """Run Gemini agent"""
    _ensure_gemini_env()
    from langchain_service.gemini_agent_bgb import create_gemini_agent_bgb

    # Create agent (Gemini modells/params via env handled innerhalb agent)
    agent = create_gemini_agent_bgb()

    # Extract user question from last user message
    user_question = None
    for msg in reversed(messages):
        if msg.get("role") == "user":
            user_question = msg.get("content")
            break

    # Extract thread_id from params if available
    thread_id = params.get("thread_id")

    if not user_question:
        raise ValidationError("No user message found in conversation history")

    # Prepare message history (all messages EXCEPT the last user message)
    message_history = [msg for msg in messages[:-1]] if len(messages) > 1 else None

    if stream:
        # Streaming not yet implemented in gemini_agent_bgb
        return _run_gemini_non_stream(agent, user_question, message_history, thread_id)
    else:
        return _run_gemini_non_stream(agent, user_question, message_history, thread_id)


def _run_gemini_non_stream(agent, user_question: str, message_history: List[Dict[str, Any]] = None, thread_id: str = None) -> Dict[str, Any]:
    """Run Gemini agent without streaming"""
    result = agent.chat(user_question, message_history=message_history, thread_id=thread_id)

    # Extract tool calls from messages
    tool_calls = []
    for msg in result.get("messages", []):
        if fn_calls := msg.get("function_calls"):
            for fn_call in fn_calls:
                tool_calls.append({
                    "name": fn_call.get("name"),
                    "arguments": str(fn_call.get("args", {}))
                })

    return {
        "content": result["final_response"],
        "usage": result.get("usage"),
        "tool_calls": tool_calls if tool_calls else None
    }


def get_available_agents() -> List[Dict[str, Any]]:
    """Get list of available agents"""
    agents = []

    # Qwen Availability
    try:
        from langchain_service.qwen_agent_bgb import create_qwen_agent_bgb
        create_qwen_agent_bgb(enable_thinking=False)
        agents.append({
            "name": "qwen",
            "description": "Qwen-based BGB assistant with function calling",
            "available": True
        })
    except Exception as e:
        logger.warning(f"Qwen agent not available: {e}")
        agents.append({
            "name": "qwen",
            "description": "Qwen-based BGB assistant (not available - Ollama required)",
            "available": False
        })

    # Gemini Availability (strict)
    gemini_available = False
    gemini_desc = "Google Gemini-based BGB assistant"

    if not settings.google_api_key:
        gemini_desc += " (not available: GOOGLE_API_KEY not set)"
    else:
        try:
            _ensure_gemini_env()
            from langchain_service.gemini_agent_bgb import create_gemini_agent_bgb
            create_gemini_agent_bgb()  # will raise if key invalid/missing
            gemini_available = True
        except Exception as e:
            logger.warning(f"Gemini agent not available: {e}")
            gemini_desc += f" (not available: {e})"

    agents.append({
        "name": "gemini",
        "description": gemini_desc,
        "available": gemini_available,
    })

    return agents
