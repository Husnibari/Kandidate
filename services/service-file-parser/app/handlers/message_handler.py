from pydantic import ValidationError as PydanticValidationError
from pika.channel import Channel
from pika.spec import Basic, BasicProperties

from services.shared_models import JobIntakeMessage
from services.shared_utils import setup_logging, ProcessingError
from ..processors import FileProcessor

logger = setup_logging("message-handler")


class MessageHandler:
    
    def __init__(self, processor: FileProcessor):
        self.processor = processor
    
    def handle_job_intake(
        self,
        ch: Channel,
        method: Basic.Deliver,
        properties: BasicProperties,
        body: bytes
    ) -> None:
        try:
            logger.info("Received job intake message")
            logger.debug(f"Message preview: {body[:200]}...")
            
            # Validate message
            job_message = JobIntakeMessage.model_validate_json(body)
            logger.info(f"[{job_message.correlation_id}] Validated job {job_message.job_id}")
            
            # Process files
            self.processor.process_job_files(job_message)
            
            logger.info(
                f"[{job_message.correlation_id}] Completed processing for job {job_message.job_id}"
            )
            
        except PydanticValidationError as e:
            logger.error(f"Message validation failed: {e}")
            logger.debug(f"Invalid message body: {body.decode('utf-8', errors='replace')}")
            
        except ProcessingError as e:
            logger.error(f"Processing failed: {e.message}")
            
        except Exception as e:
            logger.error(f"Unexpected error in callback: {e}", exc_info=True)
            
        finally:
            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.debug("Message acknowledged")
