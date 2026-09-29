from __future__ import annotations

from app.db import get_db


def get_knowledge_entries(category: str | None = None) -> list[dict]:
    with get_db() as db:
        if category:
            rows = db.execute(
                "SELECT id, category, title, content, created FROM knowledge_entries WHERE category = ? ORDER BY created DESC",
                (category,),
            ).fetchall()
        else:
            rows = db.execute(
                "SELECT id, category, title, content, created FROM knowledge_entries ORDER BY created DESC"
            ).fetchall()
    return [dict(row) for row in rows]
