'''This script is to be run to process all jobs'''

import sys, time
from pathlib import Path


# BASE_DIR should point to the directory that contains the 'api' package
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent.parent.parent

# Add BASE_DIR to sys.path
sys.path.insert(0, str(BASE_DIR))

# --------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------

# Print registered tasks
from api.core.dependencies.job_runner.app.job_manager import tool_to_script_mapping

for tool, script in tool_to_script_mapping.items():
    print(f"`{tool}` task registered ----> `{script}`")

print('\n')

# --------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------

import threading, asyncio
from uvicorn import Config, Server
from starlette.applications import Starlette
from starlette.responses import JSONResponse, StreamingResponse
from starlette.routing import Route
from starlette.requests import Request

from api.core.dependencies.job_runner.app.async_runner import job_handlers
from api.loggers.job_logger import job_logger
from api.utils.settings import settings
from api.utils.log_streamer import log_streamer
from api.utils.telex_integration import TelexIntegration


job_available_event = threading.Event()
job_lock = threading.Lock()

def job_runner():
    '''Function to run all available jobs'''

    while True:
        # Skip waiting if there are jobs in the database
        if job_handlers.check_available_jobs():  # Check if there are any jobs in the DB
            job_logger.info("New jobs available in the DB, processing immediately.")
        else:
            # Wait for a job to become available with a timeout of 60 seconds
            job_available_event.wait(60)

        try:
            # Execute jobs with job lock to ensure that jobs do not just execute as they come in
            # Especially for serial jobs that must not be executed in parallel
            # So available jobs execute as soon as the lock is released
            with job_lock:
                # Process parallel jobs first
                job_handlers.handle_parallel_jobs()

                # Process serial jobs (FFmpeg-like jobs) after parallel jobs are done
                job_handlers.handle_serial_jobs()

            # Reset the event
            job_available_event.clear()

        except Exception as exc:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            job_logger.info(f"[ERROR] - An error occured while processing jobs | {exc}, {exc_type} {exc_obj} {exc_tb.tb_lineno}")
            
            TelexIntegration(webhook_id='1e28b53611a4').push_message(
                event_name='Job Exception',
                message=f"[ERROR] - An error occured while processing jobs\n{exc}, {exc_type} {exc_obj} {exc_tb.tb_lineno}",
                status='error'
            )
        
        finally:
            # Delay before next execution
            time.sleep(5)


# ---------------------------------------------------------------------------
# ------------- LIGHTWEIGHT APP TO NOTIFY SCRIPT ABOUT NEW JOBS -------------

def root(request: Request):
    '''Root endpoint for job server'''
    
    return JSONResponse(
        status_code=200,
        content={"message": "Job server is active"}
    )
    

def notify_new_job(request: Request):
    '''Endpoint to notify the server that a job is available'''

    # Check if jobs are already running and queue the jobs that are coming in
    if job_lock.locked():
        return JSONResponse(
            status_code=202,
            content={"message": "Jobs already running. Job queued"}
        )

    # Trigger the event to notify the job runner
    job_available_event.set()
    return JSONResponse(
        status_code=200,
        content={"message": "Job notification received, processing jobs"}
    )
    

# Endpoint to stream logs
async def stream_logs(request: Request):
    """Stream the log file to the client."""

    # Get the 'lines' query parameter, defaulting to None if not provided
    lines_param = request.query_params.get("lines")
    lines = int(lines_param) if lines_param else None

    return StreamingResponse(log_streamer('logs/job_logs.log', lines), media_type="text/event-stream")


# Starlette app definition
app = Starlette(debug=True, routes=[
    Route('/', root, methods=['GET']),
    Route('/notify-job', notify_new_job, methods=['GET']),
    # Route('/logs', stream_logs, methods=['GET']),
])

# -------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------

# Set up port to listen for job notifications
def job_listener():
    '''Function to listen for job notifications'''

    # Determine port number
    if settings.PYTHON_ENV == 'prod':
        port = 7702
    elif settings.PYTHON_ENV == 'staging':
        port = 7701
    else: 
        port = 7002

    config = Config(app=app, host="0.0.0.0", port=port)
    server = Server(config)
    asyncio.run(server.serve())

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------


# Start the threads
if __name__ == "__main__":
    # Start the job processing thread
    job_thread = threading.Thread(target=job_runner)
    job_thread.start()

    # Start the uvicorn server in a separate thread
    listener_thread = threading.Thread(target=job_listener)
    listener_thread.start()

    # Wait for both threads to complete gracefully on shutdown
    job_thread.join()
    listener_thread.join()

    print("All threads have been terminated gracefully.")
    