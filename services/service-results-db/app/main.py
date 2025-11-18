import threading
import logging
import uvicorn
from .api import app
from .workers import main_worker_loop

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("results-db-main")


def start_worker():
    try:
        main_worker_loop()
    except Exception as e:
        logger.critical(f"Worker thread failed: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    logger.info("RESULTS DB SERVICE STARTING")
    
    logger.info("Starting worker thread...")
    worker_thread = threading.Thread(target=start_worker, daemon=True)
    worker_thread.start()
    logger.info("Worker thread started")
    
    logger.info("Starting API server on port 80...")
    uvicorn.run(app, host="0.0.0.0", port=80, log_level="info")

