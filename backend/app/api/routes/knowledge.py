from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional

from app.services.knowledge_service import get_knowledge_entries
from app.db import get_db

router = APIRouter()


class KnowledgeEntry(BaseModel):
    id: int
    category: str
    title: str
    content: str
    created: str


@router.get("/api/knowledge/search")
def knowledge_search(q: str = Query(..., description="Search query")):
    with get_db() as db:
        rows = db.execute(
            """
            SELECT id, category, title, content, created 
            FROM knowledge_entries 
            WHERE title LIKE ? OR content LIKE ? OR category LIKE ?
            ORDER BY created DESC
            LIMIT 20
            """,
            (f"%{q}%", f"%{q}%", f"%{q}%"),
        ).fetchall()
    
    return {"results": [dict(row) for row in rows], "query": q, "count": len(rows)}


@router.get("/api/knowledge")
def knowledge_list(category: Optional[str] = Query(None, description="Filter by category")):
    entries = get_knowledge_entries(category=category)
    return {"entries": entries, "count": len(entries)}