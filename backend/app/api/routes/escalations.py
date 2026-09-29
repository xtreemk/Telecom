from fastapi import APIRouter

from app.agents.escalation_agent import EscalationAgent

router = APIRouter()
agent = EscalationAgent()


@router.get("/api/escalations")
def escalations():
    return agent.get_queue()
