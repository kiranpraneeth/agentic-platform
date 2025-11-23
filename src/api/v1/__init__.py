"""API v1 routes."""

from fastapi import APIRouter

from src.api.v1 import agents, auth, conversations, mcp, rag, workflows

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(conversations.router, prefix="/conversations", tags=["conversations"])
api_router.include_router(rag.router, prefix="/rag", tags=["rag"])
api_router.include_router(mcp.router, prefix="/mcp", tags=["mcp"])
api_router.include_router(workflows.router, prefix="/workflows", tags=["workflows"])
