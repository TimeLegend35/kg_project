"""Agent information routes"""
from fastapi import APIRouter

from ..schemas.schemas import AgentListResponse, AgentInfo
from ..services.chat import get_available_agents

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("", response_model=AgentListResponse)
async def list_agents():
    """List available agents"""
    agents = get_available_agents()
    return AgentListResponse(
        agents=[AgentInfo(**agent) for agent in agents]
    )
"""API routes"""
