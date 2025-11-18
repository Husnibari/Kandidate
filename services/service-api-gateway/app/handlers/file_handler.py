from pathlib import Path
from typing import List, Optional
import uuid
import shutil
from fastapi import UploadFile
from services.config import settings, MAX_FILE_SIZE, ALLOWED_FILE_EXTENSIONS
from services.shared_utils import setup_logging

logger = setup_logging("file-handler")


class FileProcessingResult:
    def __init__(self, job_id: Optional[str] = None, correlation_id: Optional[str] = None):
        self.job_id = job_id or str(uuid.uuid4())
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.job_dir = Path(settings.upload_volume_path) / self.job_id
        self.saved_files = []
        self.skipped_files = []
        self.existing_file_count = 0
    
    def to_response(self) -> dict:
        response = {
            "job_id": self.job_id,
            "correlation_id": self.correlation_id,
            "status": "accepted",
            "file_count": len(self.saved_files),
            "cv_details": [
                {
                    "cv_id": file["cv_id"],
                    "original_filename": file["original_filename"]
                }
                for file in self.saved_files
            ]
        }
        
        if self.skipped_files:
            response["warnings"] = {
                "skipped_files": [f.get("filename") for f in self.skipped_files],
                "skipped_count": len(self.skipped_files),
                "message": f"{len(self.skipped_files)} file(s) were skipped due to validation errors",
                "details": self.skipped_files,
            }
        
        return response
    
    @property
    def error_detail(self) -> dict:
        return {
            "message": "All files were invalid or failed validation",
            "skipped_files": [f.get("filename") for f in self.skipped_files],
            "total_uploaded": len(self.saved_files) + len(self.skipped_files),
            "valid_files": 0
        }


def process_files(
    files: List[UploadFile], 
    existing_job_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
    existing_cv_count: int = 0
) -> FileProcessingResult:
    result = FileProcessingResult(job_id=existing_job_id, correlation_id=correlation_id)
    
    result.existing_file_count = existing_cv_count
    
    # Create directory if new job, or verify it exists for existing job
    if existing_job_id:
        if not result.job_dir.exists():
            logger.error(f"Job directory not found for existing job {existing_job_id}")
            raise ValueError(f"Job directory not found for job {existing_job_id}")
        
        logger.info(
            f"Adding {len(files)} file(s) to existing job {existing_job_id} "
            f"(has {existing_cv_count} valid CVs)"
        )
    else:
        result.job_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Processing {len(files)} file(s) for new job {result.job_id}")
    
    saved_filenames = set()
    
    # Validate Files size and type
    for idx, file in enumerate(files):
        filename = file.filename or "unknown"
        original_filename = filename
        file_ext = Path(filename).suffix.lower()
        
        skip_reason = _validate_file(file, file_ext)
        if skip_reason:
            logger.warning(f"Skipping file '{filename}': {skip_reason}")
            result.skipped_files.append({
                "filename": original_filename,
                "reason": skip_reason
            })
            continue
        
        filename = _handle_duplicate_filename(filename, saved_filenames)
        saved_filenames.add(filename)
        
        try:
            file_path = result.job_dir / filename
            with open(file_path, 'wb') as out_file:
                shutil.copyfileobj(file.file, out_file)
            
            # We offset the ID by the existing count.
            # This ensures that if a user uploads 5 files now and 3 later, 
            # the IDs remain unique and sequential.
            cv_index = result.existing_file_count + idx
            cv_id = f"{result.job_id[:8]}_{cv_index:03d}"
            result.saved_files.append({
                "cv_id": cv_id,
                "file_path": str(file_path),
                "original_filename": original_filename
            })
            logger.debug(f"Saved file: {filename} (cv_id: {cv_id})")
            
        except Exception as e:
            logger.error(f"Failed to save file '{filename}': {e}")
            result.skipped_files.append({
                "filename": original_filename,
                "reason": f"Failed to save file: {str(e)}"
            })
            continue
    
    if not result.saved_files:
        # If all files failed validation, we delete the empty directory immediately 
        # to prevent useless folders on the shared volume.
        logger.error(f"All {len(files)} files were invalid or failed to save")
        shutil.rmtree(result.job_dir, ignore_errors=True)
    else:
        logger.info(
            f"Job {result.job_id}: {len(result.saved_files)} saved, "
            f"{len(result.skipped_files)} skipped"
        )
    
    return result


def _validate_file(file: UploadFile, file_ext: str) -> str | None:
    if file_ext not in ALLOWED_FILE_EXTENSIONS:
        return (
            f"Invalid file type '{file_ext}'. "
            f"Allowed: {', '.join(ALLOWED_FILE_EXTENSIONS)}"
        )
    
    if file.size and file.size > MAX_FILE_SIZE:
        return (
            f"File too large ({file.size / 1024 / 1024:.1f}MB). "
            f"Max: {MAX_FILE_SIZE / 1024 / 1024:.1f}MB"
        )
    
    return None


def _handle_duplicate_filename(filename: str, saved_filenames: set) -> str:
    original = filename
    counter = 1
    
    while filename in saved_filenames:
        name_part = Path(original).stem
        ext_part = Path(original).suffix
        filename = f"{name_part}_{counter}{ext_part}"
        counter += 1
    
    return filename


def cleanup_job_directory(job_dir: Path):
    try:
        shutil.rmtree(job_dir, ignore_errors=True)
        logger.info(f"Cleaned up job directory: {job_dir}")
    except Exception as e:
        logger.error(f"Failed to cleanup job directory {job_dir}: {e}")


def cleanup_files(files_list: List[dict], job_dir: Path):
    try:
        for file_info in files_list:
            file_path = Path(file_info.get("file_path", ""))
            if file_path.exists():
                file_path.unlink()
                logger.debug(f"Cleaned up file: {file_path}")
        logger.info(f"Cleaned up {len(files_list)} file(s) from {job_dir}")
    except Exception as e:
        logger.error(f"Failed to cleanup job directory {job_dir}: {e}")
