from fastapi import APIRouter, HTTPException
import logging

from ..database.operations import (
    get_job,
    create_job,
    add_files_to_job,
    delete_job,
    update_job_status
)
from ..database.models import (
    CreateJobRequest,
    AddFilesRequest,
    UpdateStatusRequest
)

logger = logging.getLogger("results-db-routes")

router = APIRouter()


@router.get("/")
async def health_check():
    return {
        "service": "results-db",
        "status": "healthy",
        "version": "1.0.0"
    }


@router.get("/results/{job_id}",
    summary="Get Job Results",
    description="Retrieve results and status for a specific job"
)
async def get_results(job_id: str):
    logger.info(f"Results requested for job {job_id}")
    
    job = await get_job(job_id)
    if not job:
        logger.warning(f"Job {job_id} not found")
        raise HTTPException(status_code=404, detail="Job not found")
    
    logger.debug(f"Returning job {job_id} with status: {job.get('status', 'unknown')}")
    return job


@router.post("/jobs",
    summary="Create Job",
    description="Create a new job record in the database"
)
async def create_new_job(request: CreateJobRequest):
    logger.info(
        f"[{request.correlation_id}] Creating job {request.job_id} "
        f"with {request.file_count} expected file(s)"
    )
    
    job = await create_job(
        request.job_id,
        request.correlation_id,
        request.jd_text,
        request.file_count
    )
    
    logger.info(f"[{request.correlation_id}] Job {request.job_id} created successfully")
    return job


@router.patch("/jobs/{job_id}/add-files",
    summary="Add Files to Job",
    description="Increment the expected files count for an existing job"
)
async def add_files_to_existing_job(job_id: str, request: AddFilesRequest):
    logger.info(f"Adding {request.file_count} files to job {job_id}")
    
    success = await add_files_to_job(job_id, request.file_count)
    
    if not success:
        logger.warning(f"Job {job_id} not found")
        raise HTTPException(status_code=404, detail="Job not found")
    
    logger.info(f"Added {request.file_count} files to job {job_id}")
    
    job = await get_job(job_id)
    return job


@router.delete("/jobs/{job_id}",
    summary="Delete Job",
    description="Delete job from MongoDB after archiving to PostgreSQL"
)
async def delete_existing_job(job_id: str):
    logger.info(f"Deleting job {job_id} from MongoDB")
    
    success = await delete_job(job_id)
    
    if not success:
        logger.warning(f"Job {job_id} not found for deletion")
        raise HTTPException(status_code=404, detail="Job not found")
    
    logger.info(f"Deleted job {job_id} from MongoDB")
    
    return {"message": f"Job {job_id} deleted successfully"}


@router.patch("/jobs/{job_id}/status",
    summary="Update Job Status",
    description="Update the status of an existing job"
)
async def update_job_status_route(job_id: str, request: UpdateStatusRequest):
    logger.info(f"Updating job {job_id} status to '{request.status}'")
    
    success = await update_job_status(job_id, request.status)
    
    if not success:
        logger.warning(f"Job {job_id} not found for status update")
        raise HTTPException(status_code=404, detail="Job not found")
    
    logger.info(f"Updated job {job_id} status to '{request.status}'")
    
    job = await get_job(job_id)
    return job

