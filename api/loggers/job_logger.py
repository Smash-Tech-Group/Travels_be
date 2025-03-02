import logging

# Configure the logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s: %(message)s",
    handlers=[logging.FileHandler("logs/job_logs.log"), logging.StreamHandler()],
)

job_logger = logging.getLogger(__name__)
