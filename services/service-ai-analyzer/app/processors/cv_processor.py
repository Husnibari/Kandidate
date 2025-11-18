import time
import json
from typing import Dict, Any, Optional, Literal
from pydantic import ValidationError as PydanticValidationError
from pika.channel import Channel

from services.shared_models import AnalysisResult, JobResultMessage
from services.shared_utils import publish_message, setup_logging
from services.config import QUEUE_RESULTS_STORAGE, AI_RATE_LIMIT_DELAY
from ..analyzers import GeminiAnalyzer

logger = setup_logging("cv-processor")


class CVProcessor:
    
    def __init__(self, analyzer: GeminiAnalyzer, channel: Channel):
        self.analyzer = analyzer
        self.channel = channel
    
    def process_cv(
        self,
        cv_data: Dict[str, Any],
        jd_text: str,
        job_id: str,
        correlation_id: str,
        cv_index: int,
        total_cvs: int,
        use_delay: bool = False
    ) -> None:
        cv_id = cv_data.get('cv_id', f'unknown_{cv_index}')
        cv_text = cv_data.get('text', '')
        filename = cv_data.get('filename', f'cv_{cv_index}')
        original_filename = cv_data.get('original_filename', filename)
        
        logger.info(f"[{correlation_id}] Analyzing CV {cv_index}/{total_cvs}: {filename} (cv_id: {cv_id})")
        
        if use_delay:
            # We block the worker thread intentionally here. 
            # Since prefetch_count=1, sleeping here guarantees we don't pull the next message
            # until the rate limit window (5s) has passed, keeping us free-tier compliant.
            logger.debug(f"[{correlation_id}] Applying rate limit delay: {AI_RATE_LIMIT_DELAY}s")
            time.sleep(AI_RATE_LIMIT_DELAY)
        
        try:
            logger.debug(f"[{correlation_id}] Sending CV to Gemini API (length: {len(cv_text)} chars)")
            result = self.analyzer.analyze_cv(cv_text, jd_text)
            
            # The AI output is pure data. It doesn't know about our DB IDs.
            # We inject the 'cv_id' back into the result object here so the Storage Service 
            # knows exactly which record to update in MongoDB/Postgres.
            result.cv_id = cv_id
            result.original_filename = original_filename
            
            self._publish_result(
                job_id=job_id,
                correlation_id=correlation_id,
                cv_id=cv_id,
                filename=original_filename,
                status="success",
                data=result
            )
            
            logger.info(
                f"[{correlation_id}] Successfully analyzed {filename} "
                f"(cv_id: {cv_id}, score: {result.match_score}/100)"
            )
            
        except (json.JSONDecodeError, PydanticValidationError) as e:
            logger.error(f"[{correlation_id}] AI validation failed for {filename} (cv_id: {cv_id}): {str(e)[:200]}")
            error_msg = f"AI Validation Error: {str(e)[:200]}"
            # If this specific CV fails validation, we publish an error status 
            # but we DO NOT crash the worker. This allows the rest of the batch to complete.
            self._publish_result(
                job_id=job_id,
                correlation_id=correlation_id,
                cv_id=cv_id,
                filename=original_filename,
                status="error",
                error=error_msg
            )
            
        except Exception as e:
            logger.error(f"[{correlation_id}] Gemini API error for {filename} (cv_id: {cv_id}): {e}", exc_info=True)
            error_msg = f"Gemini API Error: {str(e)}"
            self._publish_result(
                job_id=job_id,
                correlation_id=correlation_id,
                cv_id=cv_id,
                filename=original_filename,
                status="error",
                error=error_msg
            )
    
    def _publish_result(
        self,
        job_id: str,
        correlation_id: str,
        cv_id: str,
        filename: str,
        status: Literal['success', 'error'],
        data: Optional[AnalysisResult] = None,
        error: Optional[str] = None
    ) -> None:
        try:
            result_message = JobResultMessage(
                job_id=job_id,
                correlation_id=correlation_id,
                cv_id=cv_id,
                original_filename=filename,
                status=status,
                data=data,
                error=error
            )
            
            publish_message(self.channel, QUEUE_RESULTS_STORAGE, result_message, logger=logger)
            
            if status == "success":
                logger.debug(f"[{correlation_id}] Published successful result for {filename}")
            else:
                logger.debug(f"[{correlation_id}] Published error result for {filename}")
                
        except Exception as e:
            logger.error(f"[{correlation_id}] Failed to publish result for {filename}: {e}", exc_info=True)
