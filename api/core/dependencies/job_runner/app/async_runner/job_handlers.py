import requests

from api.core.dependencies.job_runner.app.async_runner import thread_config
from api.core.dependencies.job_runner.app.services import regular_service
from api.utils.settings import settings
from api.loggers.job_logger import job_logger
from api.db.database import get_db
from api.v1.models.job import JobStatus
from api.v1.services.job import tifi_job_service


def fetch_and_mark_jobs_as_processing(fetch_parallel: bool=True):
    '''This function fetches all jobs from the database'''

    try:
        url = f'{settings.APP_URL}/api/v1/jobs/retrieve-and-mark-as-processing?is_parallel={fetch_parallel}'
        response = requests.get(url=url)

        if response.status_code == 200:
            jobs = response.json()['data']

            # Check for available jobs
            if len(jobs) == 0:
                job_logger.info('No jobs available at this time')
                return None
            
            return jobs
        else:
            job_logger.info(f'Error retrieving jobs: {response.status_code} - {response.json()} - {url}')
            return None
        
    except Exception as e:
        job_logger.info(f'Error fetching and marking jobs as processing: {str(e)}')
        return None


def handle_parallel_jobs():
    '''This function handles jobs that can be processed in parallel to each other'''

    # Get all marked as processing jobs
    jobs = fetch_and_mark_jobs_as_processing(fetch_parallel=True)

    if not jobs:
        return

    job_logger.info('Running parallel jobs')
    
    futures = []
    
    # Submit jobs to ThreadPoolExecutor
    for job in jobs:
        futures.append(thread_config.parallel_executor.submit(regular_service.process_job, job['id'], True))

    # Wait for all parallel jobs to complete
    for future in futures:
        future.result()
    
    job_logger.info('All parallel jobs completed')


def handle_serial_jobs():
    '''This function handles heavy jobs that mus be processed one by one'''

    # Get all marked as processing jobs
    jobs = fetch_and_mark_jobs_as_processing(fetch_parallel=False)

    if not jobs:
        return

    job_logger.info('Running serial jobs')

    # Process serial jobs one by one
    for job in jobs:
        with thread_config.db_lock:
            regular_service.process_job(job['id'], with_lock=True)
    
    job_logger.info('All serial jobs processed')


def check_available_jobs():
    '''Returns true if there are any available jobs in the db ready for processing'''

    db = next(get_db())

    # Get pending jobs ready for processing
    jobs = tifi_job_service.fetch_jobs_by_status(db, JobStatus.pending)
    return len(jobs) > 0
