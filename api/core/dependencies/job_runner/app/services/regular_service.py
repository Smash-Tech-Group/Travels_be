import json, os, secrets
from pathlib import Path
import sys
import time, subprocess
from datetime import datetime
from sqlalchemy import asc

from api.core.dependencies.job_runner.app.job_manager import tool_to_script_mapping
from api.core.dependencies.job_runner.app.utils import parse_json_string
from api.db.database import get_db, SessionLocal
from api.utils.telex_integration import TelexIntegration
from api.v1.services.user import user_service
from api.v1.services.notification import notification_service
from api.v1.services.job import tifi_job_service
from api.v1.models.job import TifiJob, JobStatus
from api.loggers.job_logger import job_logger
from api.core.dependencies.email.email_sender import send_email


BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent.parent.parent


def run_job_script(job: TifiJob):
    '''THis function runs the tool to run the job script for each job'''

    try:
        job_payload = job.payload
        job_payload['job_id'] = job.id

        # Convert the payload to a JSON string
        payload_str = json.dumps(job_payload)

        # Get script path based on the task name
        script_path = tool_to_script_mapping.get(job.tool_name, None)

        if not script_path:
            raise ValueError(f"No script found for tool: {job.tool_name}")

        # Set PYTHONPATH in environment variables to the root directory
        env = os.environ.copy()
        env["PYTHONPATH"] = BASE_DIR

        process = subprocess.Popen(
            ['python3', '-u', script_path, payload_str],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            bufsize=1
        )

        # Stream output in real-time
        result_output = ''
        for line in iter(process.stdout.readline, ''):
            # print(line)
            job_logger.info(line)
            result_output = line.strip()  # get the last line printed out to the console

        # Ensure the process is finished
        process.stdout.close()
        return_code = process.wait()

        # If there's an error, capture stderr and raise an exception
        if return_code != 0:
            stderr_output = process.stderr.read()
            process.stderr.close()
            raise Exception(f"{stderr_output}")
        
        return result_output
    
    except subprocess.CalledProcessError as e:
        raise e
        
    except Exception as e:
        raise e

def process_job(job_id: str, with_lock: bool = False):
    '''This function processes a job and updates the status of the job'''

    db = next(get_db())

    # Fetch job
    if with_lock:
        job = tifi_job_service.fetch_with_lock(db=db, job_id=job_id)
    else:
        job = tifi_job_service.fetch(db=db, job_id=job_id)

    try:
        job.status = JobStatus.progress
        db.commit()

        output = run_job_script(job)

        job.status = JobStatus.completed
        job.result = parse_json_string(output)
        db.commit()

        if job.user_id:
            # Send notification to the user            
            user = user_service.fetch(db, job.user_id)
            notification_service.send_notification(
                db=db,
                user=user,
                title="Job successful",
                message=f"The job for '{job.tool_name}' was successful",
                type='success'
            )
            
            # Send email to user
            # await send_email(
            #     recipient=user.email,
            #     template_name='job-successful.html',
            #     subject=f'{job.tool_name} job successful',
            #     context={
            #         # "request": request,
            #         "user": user,
            #         "job": job,
            #         # "url": "https://tifi.tv"
            #     }
            # )
            
    
        # Save job as completed
        job.progress = '100% complete'
        job.status_message = 'Job completed successfully'
        db.commit()

        print(f'Job {job.id} completed\n')
        job_logger.info(f'Job {job.id} completed\n')

    except Exception as e:
        job.status = JobStatus.failed
        job.status_message = str(e)
        db.commit()
        db.refresh(job)

        if job.user_id:
            # Send notification to the user
            user = user_service.fetch(db, job.user_id)
            notification_service.send_notification(
                db=db,
                user=user,
                title="Job failed",
                message=f"The job '{job.tool_name}' was unsuccessful",
                type='warning'
            )
            
            # await send_email(
            #     recipient=user.email,
            #     template_name='job-failed.html',
            #     subject=f'{job.tool_name} job failed',
            #     context={
            #         # "request": request,
            #         "user": user,
            #         "job": job,
            #         # "url": "https://tifi.tv"
            #     }
            # )
        
        # print(f'Job with {job.id} for tool {job.tool_name} failed')
        # print(f'An exception occured: {str(e)}')
        # job_logger.info(f'Error processing job {job_id}: {str(e)}')
        exc_type, exc_obj, exc_tb = sys.exc_info()
        job_logger.info(f"[ERROR] - An error occured while processing job {job_id}\n{e}, {exc_type} {exc_obj} {exc_tb.tb_lineno}")
        
        TelexIntegration(webhook_id='1e28b53611a4').push_message(
            event_name='Job Exception',
            message=f"[ERROR] - An error occured while processing job {job_id}\n{e}, {exc_type} {exc_obj} {exc_tb.tb_lineno}",
            status='error'
        )


def run_available_jobs():
    '''This function checks for and runs all pending jobs in the database'''

    while True:
        with SessionLocal() as db:
            current_time = datetime.now().replace(tzinfo=None)

            query = db.query(TifiJob).filter(
                TifiJob.status == JobStatus.processing,
                TifiJob.expiration_time >= current_time,
            ).order_by(asc(TifiJob.created_at))

            # Get all premium jobs i.e jobs for a premium user
            premium_jobs = query.filter(TifiJob.is_premium == True,).all()

            # Get all free jobs i.e jobs for a free user
            free_jobs = query.filter(TifiJob.is_premium == False,).all()

            # Get all jobs
            all_pending_jobs = query.all()
            
            no_of_jobs = len(all_pending_jobs)
            if no_of_jobs > 0:
                for job_obj in all_pending_jobs:
                    try:
                        process_job(job_id=job_obj.id)
                    except Exception as e:
                        print(f"Error processing job {job_obj.id}: {e}")
                    
                    time.sleep(2)
            else:
                print('No pending jobs available')
                
            break
