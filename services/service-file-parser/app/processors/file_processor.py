from pathlib import Path
from typing import Dict, Any, List
from pika.channel import Channel

from services.shared_models import JobIntakeMessage, BatchAnalysisMessage
from services.shared_utils import publish_message, setup_logging
from services.config import QUEUE_AI_ANALYSIS, QUEUE_RESULTS_STORAGE
from ..parsers import extract_text_from_pdf, extract_text_from_docx
from ..utils import publish_error_result

logger = setup_logging("file-processor")


class FileProcessor:
    def __init__(self, channel: Channel):
        self.channel = channel
    
    def process_job_files(self, job_message: JobIntakeMessage) -> None:
        cv_texts = []
        
        logger.info(
            f"[{job_message.correlation_id}] Processing {len(job_message.file_paths)} file(s) "
            f"for job {job_message.job_id}"
        )
        
        for file_info in job_message.file_paths:
            result = self._process_single_file(
                file_info,
                job_message.job_id,
                job_message.correlation_id
            )
            
            if result:
                cv_texts.append(result)
        
        if cv_texts:
            self._publish_batch_for_analysis(job_message, cv_texts)
        else:
            logger.warning(
                f"[{job_message.correlation_id}] No files successfully processed "
                f"for job {job_message.job_id}"
            )
    
    def _process_single_file(
        self,
        file_info: Dict[str, Any],
        job_id: str,
        correlation_id: str
    ) -> Dict[str, Any] | None:
        cv_id = file_info["cv_id"]
        file_path_str = file_info["file_path"]
        original_filename = file_info["original_filename"]
        filename = Path(file_path_str).name
        
        try:
            file_path = Path(file_path_str)
            
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path_str}")
            
            suffix = file_path.suffix.lower()
            
            logger.debug(
                f"[{correlation_id}] Extracting text from {filename} "
                f"(cv_id: {cv_id}, {suffix})"
            )
            
            # Extract text based on file type
            if suffix == '.pdf':
                raw_text = extract_text_from_pdf(file_path)
            elif suffix == '.docx':
                raw_text = extract_text_from_docx(file_path)
            else:
                raise ValueError(f"Unsupported file format: {suffix}")
            
            logger.info(
                f"[{correlation_id}] Extracted {len(raw_text)} characters from "
                f"{filename} (cv_id: {cv_id})"
            )
            
            return {
                "cv_id": cv_id,
                "filename": filename,
                "original_filename": original_filename,
                "text": raw_text
            }
            
        except Exception as e:
            error_type = type(e).__name__
            logger.error(
                f"[{correlation_id}] {error_type} while processing {filename} (cv_id: {cv_id}): {e}",
                exc_info=not isinstance(e, (FileNotFoundError, ValueError))
            )
            publish_error_result(
                self.channel, job_id, correlation_id, cv_id, original_filename, str(e)
            )
            return None
    
    def _publish_batch_for_analysis(
        self,
        job_message: JobIntakeMessage,
        cv_texts: List[Dict[str, Any]]
    ) -> None:
        logger.info(
            f"[{job_message.correlation_id}] Publishing {len(cv_texts)} CV(s) "
            f"for AI analysis"
        )
        
        batch_message = BatchAnalysisMessage(
            job_id=job_message.job_id,
            correlation_id=job_message.correlation_id,
            jd_text=job_message.jd_text,
            use_delay=job_message.use_delay,
            cvs=cv_texts
        )
        
        publish_message(self.channel, QUEUE_AI_ANALYSIS, batch_message, logger=logger)
        logger.info(f"[{job_message.correlation_id}] Published batch for job {job_message.job_id}")
