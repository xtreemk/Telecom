from fastapi import APIRouter

from app.services.ticket_service import get_tickets

router = APIRouter()


@router.get("/api/tickets")
def tickets():
    return get_tickets()
