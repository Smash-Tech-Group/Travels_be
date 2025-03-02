import json, os
from pathlib import Path
import time, subprocess
from datetime import datetime
from sqlalchemy import asc

from api.core.dependencies.job_runner.app.job_manager import tool_to_script_mapping
from api.core.dependencies.job_runner.app.utils import parse_json_string
from api.db.database import get_db, SessionLocal
from api.v1.services.notification import notification_service
from api.v1.services.user import user_service
from api.v1.services.job import tifi_job_service
from api.v1.models.job import TifiJob, JobStatus


# Get project root directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent.parent.parent


def run_job_script(job: TifiJob):
    '''THis function runs the tool to run the job script for each job'''

    try:
        yield f'Job with id {job.id} for tool {job.tool_name} in execution\n'

        job_payload = job.payload
        job_payload['job_id'] = job.id

        # Convert the payload to a JSON string
        payload_str = json.dumps(job_payload)

        # Get script path based on the task name
        script_path = tool_to_script_mapping.get(job.tool_name, None)

        if not script_path:
            yield f"No script found for tool: {job.tool_name}"
            raise ValueError(f"No script found for tool: {job.tool_name}")
        
        yield f'Opening script {script_path} for job {job.id} and tool {job.tool_name}\n'

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
        while True:
            output_line = process.stdout.readline()
            if output_line:
                yield output_line
                result_output = output_line.strip()  # Capture the last line in real-time
            if process.poll() is not None:
                break

        # Ensure the process is finished
        process.stdout.close()
        return_code = process.wait()

        # If there's an error, capture stderr and raise an exception
        if return_code != 0:
            stderr_output = process.stderr.read()
            process.stderr.close()
            # yield f"Job failed with error: {stderr_output}"
            raise Exception(f"{stderr_output}")
        
        yield f'Closing script {script_path}\n'       

        # If the final output is empty, handle it
        if not result_output:
            raise Exception("No output returned from job script") 

        # return result_output
        yield f'{result_output}\n'
    
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
        # Mark job as in progress
        job.status = JobStatus.progress
        db.commit()
        
        # # Call the tool to process the job and yield outputs
        result = None
        for output in run_job_script(job):
            # Yield the result for streaming
            yield output
            # Capture only the final result returned by run_job_script
            result = output

        job.status = JobStatus.completed
        job.result = parse_json_string(result)
        db.commit()

        if job.user_id:
            # Send notification to the user
            yield 'Sending notification to the user\n'

            user = user_service.fetch(db, job.user_id)
            notification_service.send_notification(
                db=db,
                user=user,
                title="Job successful",
                message=f"The job for '{job.tool_name}' was successful",
                type='success'
            )
        
        # Save job as completed
        job.progress = '100% complete'
        job.status_message = 'Job completed successfully'
        db.commit()
        yield f'Job {job.id} progress information: Job completed\n\n'

    except Exception as e:
        # Update job status to failed
        job.status = JobStatus.failed
        job.status_message = str(e)
        db.commit()
        db.refresh(job)
        
        if job.user_id:
            # Send notification to the user
            yield 'Sending notification to the user\n'

            user = user_service.fetch(db, job.user_id)
            notification_service.send_notification(
                db=db,
                user=user,
                title="Job failed",
                message=f"The job '{job.tool_name}' was unsuccessful",
                type='warning'
            )

        yield f'Job with {job.id} for tool {job.tool_name} failed\n'
        yield f'An exception occured: {str(e)}\n\n'


def run_available_jobs():
    '''This function checks for and runs all pending jobs in the database'''

    while True:
        with SessionLocal() as db:
            current_time = datetime.now().replace(tzinfo=None)
            
            yield f'Fetching number of available jobs to be processed\n'

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
                yield f'Number of jobs to be processed: {no_of_jobs}\n'

                for job_obj in all_pending_jobs:
                    try:
                        yield f'Job with id {job_obj.id} for tool {job_obj.tool_name} in progress\n'
                        
                        # Yield the output from process_job
                        for output in process_job(job_id=job_obj.id):
                            yield output

                    except Exception as e:
                        yield f"Error processing job {job_obj.id}: {e}\n"
                    
                    time.sleep(2)
                
                yield f'All jobs processed and executed successfully\n'
            else:     
                yield 'No pending jobs available\n'
                
            break
