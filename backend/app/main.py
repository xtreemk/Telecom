from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.chat import router as chat_router
from app.api.routes.conversations import router as conversations_router
from app.api.routes.customers import router as customers_router
from app.api.routes.escalations import router as escalations_router
from app.api.routes.health import router as health_router
from app.api.routes.knowledge import router as knowledge_router
from app.api.routes.reports import router as reports_router
from app.api.routes.tickets import router as tickets_router
from app.api.routes.voice import router as voice_router
from app.config import settings

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(customers_router)
app.include_router(chat_router)
app.include_router(tickets_router)
app.include_router(reports_router)
app.include_router(escalations_router)
app.include_router(voice_router)
app.include_router(knowledge_router)
app.include_router(conversations_router)
