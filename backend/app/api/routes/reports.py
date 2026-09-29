from fastapi import APIRouter

from app.agents.reporting_agent import ReportingAgent

router = APIRouter()
reporting_agent = ReportingAgent()


@router.get("/api/reports/overview")
def reports_overview():
    return reporting_agent.overview()


@router.get("/api/reports/intents")
def reports_intents():
    return reporting_agent.intents()


@router.get("/api/reports/agents")
def reports_agents():
    return reporting_agent.agents()


@router.get("/api/reports/escalations")
def reports_escalations():
    return reporting_agent.escalations()


@router.get("/api/reports/transactions")
def reports_transactions():
    return reporting_agent.transactions()
