"""AI Layer — API router."""
from fastapi import APIRouter
from app.core.dependencies import DBSession

router = APIRouter(prefix="/ai", tags=["AI Layer Debug & Admin"])

@router.post("/parse-resume-debug", summary="Debug parser endpoint")
async def debug_parse(db: DBSession): raise NotImplementedError("Sprint 2")
