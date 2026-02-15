"""System endpoints: health check, scheduler control."""

import logging

from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "FinancialMarketWatchdog"}


@router.get("/jobs")
def list_jobs():
    """List all scheduled jobs."""
    from app.scheduler import get_scheduler

    scheduler = get_scheduler()
    if not scheduler:
        return {"status": "error", "message": "Scheduler not initialized"}

    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
        })

    return {"status": "ok", "jobs": jobs}


class JobTriggerRequest(BaseModel):
    job_id: str


@router.post("/jobs/trigger")
def trigger_job(req: JobTriggerRequest):
    """Manually trigger a scheduled job."""
    from app.scheduler import get_scheduler

    scheduler = get_scheduler()
    if not scheduler:
        return {"status": "error", "message": "Scheduler not initialized"}

    job = scheduler.get_job(req.job_id)
    if not job:
        return {"status": "error", "message": f"Job '{req.job_id}' not found"}

    job.modify(next_run_time=None)
    return {"status": "ok", "message": f"Job '{req.job_id}' triggered"}


@router.post("/jobs/{job_id}/pause")
def pause_job(job_id: str):
    """Pause a scheduled job."""
    from app.scheduler import get_scheduler

    scheduler = get_scheduler()
    if not scheduler:
        return {"status": "error", "message": "Scheduler not initialized"}

    job = scheduler.get_job(job_id)
    if not job:
        return {"status": "error", "message": f"Job '{job_id}' not found"}

    scheduler.pause_job(job_id)
    return {"status": "ok", "message": f"Job '{job_id}' paused"}


@router.post("/jobs/{job_id}/resume")
def resume_job(job_id: str):
    """Resume a paused job."""
    from app.scheduler import get_scheduler

    scheduler = get_scheduler()
    if not scheduler:
        return {"status": "error", "message": "Scheduler not initialized"}

    job = scheduler.get_job(job_id)
    if not job:
        return {"status": "error", "message": f"Job '{job_id}' not found"}

    scheduler.resume_job(job_id)
    return {"status": "ok", "message": f"Job '{job_id}' resumed"}
