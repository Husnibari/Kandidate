from pydantic import ValidationError as PydanticValidationError
from pika.channel import Channel
from pika.spec import Basic, BasicProperties

from services.shared_models import BatchAnalysisMessage
from services.shared_utils import setup_logging
from ..processors import CVProcessor

logger = setup_logging("message-handler")


class MessageHandler:
    
    def __init__(self, processor: CVProcessor):
        self.processor = processor
    
    def handle_batch_message(
        self,
        ch: Channel,
        method: Basic.Deliver,
        properties: BasicProperties,
        body: bytes
    ) -> None:
        try:
            logger.info("Received batch analysis message")
            logger.debug(f"Message preview: {body[:200]}...")
            
            message = BatchAnalysisMessage.model_validate_json(body)
            logger.info(
                f"[{message.correlation_id}] Validated job {message.job_id} "
                f"with {len(message.cvs)} CV(s)"
            )
            
            for idx, cv_data in enumerate(message.cvs, 1):
                self.processor.process_cv(
                    cv_data=cv_data,
                    jd_text=message.jd_text,
                    job_id=message.job_id,
                    correlation_id=message.correlation_id,
                    cv_index=idx,
                    total_cvs=len(message.cvs),
                    use_delay=message.use_delay
                )
            
            logger.info(f"[{message.correlation_id}] Completed analysis for job {message.job_id}")
            
        except PydanticValidationError as e:
            logger.error(f"Message validation failed: {e}")
            logger.debug(f"Invalid message body: {body.decode('utf-8', errors='replace')}")
            
        except Exception as e:
            logger.error(f"Unexpected error in message handler: {e}", exc_info=True)
            
        finally:
            # We ACK even if validation fails. Why?
            # If the JSON is malformed, retrying will never fix it. It will just loop forever.
            # We must remove it from the queue to prevent clogging the consumer.
            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.debug("Message acknowledged")
