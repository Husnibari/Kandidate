import httpx
from fastapi import HTTPException
from services.config import settings
from services.shared_utils import setup_logging

logger = setup_logging("results-db-client")


async def create_job(job_id: str, correlation_id: str, jd_text: str, file_count: int):
    logger.info(f"[{correlation_id}] Creating job {job_id} in results-db")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(
                f"{settings.results_db_url}/jobs",
                json={
                    "job_id": job_id,
                    "correlation_id": correlation_id,
                    "jd_text": jd_text,
                    "file_count": file_count
                }
            )
            
            if response.status_code != 200:
                logger.error(
                    f"[{correlation_id}] Results-db job creation failed: "
                    f"{response.status_code} - {response.text}"
                )
                raise HTTPException(
                    status_code=503,
                    detail=f"Failed to create job in results-db: {response.text}"
                )
            
            logger.info(f"[{correlation_id}] Job {job_id} created in results-db")
            
        except httpx.RequestError as e:
            logger.error(f"[{correlation_id}] Failed to connect to results-db: {e}")
            raise HTTPException(
                status_code=503,
                detail=f"service-results-db is unreachable: {e}"
            )


async def add_files_to_job(job_id: str, file_count: int):
    logger.info(f"Adding {file_count} files to job {job_id}")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.patch(
                f"{settings.results_db_url}/jobs/{job_id}/add-files",
                json={"file_count": file_count}
            )
            
            if response.status_code != 200:
                logger.error(
                    f"Failed to add files to job {job_id}: "
                    f"{response.status_code} - {response.text}"
                )
                raise HTTPException(
                    status_code=503,
                    detail=f"Failed to update job in results-db: {response.text}"
                )
            
            logger.info(f"Successfully added {file_count} files to job {job_id}")
            
        except httpx.RequestError as e:
            logger.error(f"Failed to connect to results-db: {e}")
            raise HTTPException(
                status_code=503,
                detail=f"service-results-db is unreachable: {e}"
            )


async def get_job(job_id: str) -> dict:

    logger.info(f"Status check requested for job {job_id}")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(
                f"{settings.results_db_url}/results/{job_id}"
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Job {job_id} status: {result.get('status', 'unknown')}")
            return result
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Job {job_id} not found")
            else:
                logger.error(
                    f"Results-db error for job {job_id}: "
                    f"{e.response.status_code}"
                )
            raise HTTPException(
                status_code=e.response.status_code,
                detail=str(e.response.text)
            )
        except httpx.RequestError as e:
            logger.error(f"Failed to connect to results-db: {e}")
            raise HTTPException(
                status_code=503,
                detail=f"service-results-db is unreachable: {e}"
            )


async def delete_job(job_id: str):
    logger.info(f"Deleting job {job_id} from MongoDB")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.delete(
                f"{settings.results_db_url}/jobs/{job_id}"
            )
            
            if response.status_code != 200:
                logger.error(
                    f"Failed to delete job {job_id}: "
                    f"{response.status_code} - {response.text}"
                )
                raise HTTPException(
                    status_code=503,
                    detail=f"Failed to delete job from results-db: {response.text}"
                )
            
            logger.info(f"Successfully deleted job {job_id} from MongoDB")
            
        except httpx.RequestError as e:
            logger.error(f"Failed to connect to results-db: {e}")
            raise HTTPException(
                status_code=503,
                detail=f"service-results-db is unreachable: {e}"
            )


async def update_job_status(job_id: str, status: str):
    logger.info(f"Updating job {job_id} status to '{status}'")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.patch(
                f"{settings.results_db_url}/jobs/{job_id}/status",
                json={"status": status}
            )
            
            if response.status_code != 200:
                logger.error(
                    f"Failed to update status for job {job_id}: "
                    f"{response.status_code} - {response.text}"
                )
                raise HTTPException(
                    status_code=503,
                    detail=f"Failed to update job status in results-db: {response.text}"
                )
            
            logger.info(f"Successfully updated job {job_id} status to '{status}'")
            
        except httpx.RequestError as e:
            logger.error(f"Failed to connect to results-db: {e}")
            raise HTTPException(
                status_code=503,
                detail=f"service-results-db is unreachable: {e}"
            )

