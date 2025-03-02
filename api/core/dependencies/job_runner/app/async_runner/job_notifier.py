import requests
from api.utils.settings import settings
from api.loggers.app_logger import app_logger


def notify_job_runner():
    url = f"{settings.JOB_APP_URL}/notify-job"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            app_logger.info("Job runner notified successfully")
        elif response.status_code == 202:
            app_logger.info("Job queued in job runner")
        else:
            app_logger.info(f"Failed to notify job runner: {response.status_code}")
    except Exception as e:
        app_logger.info(f"Error notifying job runner: {e}")
