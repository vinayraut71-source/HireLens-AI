"""Applications module — API router. PRD Section 8.7 + 8.9."""
from uuid import UUID
from fastapi import APIRouter
from app.core.dependencies import DBSession

router = APIRouter(prefix="/applications", tags=["Applications & Tracking"])

@router.post("", status_code=201, summary="Track new application")
async def create_application(db: DBSession): raise NotImplementedError("Sprint 6")
@router.get("", summary="List applications")
async def list_applications(db: DBSession): raise NotImplementedError("Sprint 6")
@router.get("/stats", summary="Get application statistics")
async def get_stats(db: DBSession): raise NotImplementedError("Sprint 6")
@router.get("/{app_id}", summary="Get application details")
async def get_application(app_id: UUID, db: DBSession): raise NotImplementedError("Sprint 6")
@router.patch("/{app_id}", summary="Update application status/notes")
async def update_application(app_id: UUID, db: DBSession): raise NotImplementedError("Sprint 6")
@router.delete("/{app_id}", status_code=204, summary="Delete application")
async def delete_application(app_id: UUID, db: DBSession): raise NotImplementedError("Sprint 6")

# --- Outcome Tracking (PRD 8.7) ---
@router.post("/{app_id}/outcomes", status_code=201, summary="Record job outcome event")
async def record_outcome(app_id: UUID, db: DBSession): raise NotImplementedError("Sprint 6")
@router.get("/{app_id}/outcomes", summary="Get outcome history")
async def get_outcomes(app_id: UUID, db: DBSession): raise NotImplementedError("Sprint 6")

# --- Human-in-the-Loop Tailoring Packages (PRD 8.9) ---
package_router = APIRouter(prefix="/applications/packages", tags=["Application Packages (HITL)"])

@router.post("/packages", status_code=201, summary="Create a tailored package")
async def create_package(db: DBSession): raise NotImplementedError("Phase 2")
@router.get("/packages", summary="List tailored packages")
async def list_packages(db: DBSession): raise NotImplementedError("Phase 2")
@router.get("/packages/{pkg_id}", summary="Get package details")
async def get_package(pkg_id: UUID, db: DBSession): raise NotImplementedError("Phase 2")
@router.post("/packages/{pkg_id}/approve", summary="Approve tailored package")
async def approve_package(pkg_id: UUID, db: DBSession): raise NotImplementedError("Phase 2")
@router.post("/packages/{pkg_id}/reject", summary="Reject tailored package")
async def reject_package(pkg_id: UUID, db: DBSession): raise NotImplementedError("Phase 2")
@router.post("/packages/{pkg_id}/submit", summary="Submit package to job posting")
async def submit_package(pkg_id: UUID, db: DBSession): raise NotImplementedError("Phase 2")
