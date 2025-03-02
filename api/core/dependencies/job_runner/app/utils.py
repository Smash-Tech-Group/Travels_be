import json, threading, os, time, ffmpeg, subprocess, re
from uuid import uuid4
from typing import Optional
from sqlalchemy.orm import Session

from api.utils.settings import settings
from api.v1.models.job import TifiJob
from api.loggers.job_logger import job_logger


def save_and_print_job_progress(
    db: Session, 
    job: TifiJob, 
    progress: int,
    progress_info: Optional[str] = None
):
    if progress_info:
        print(f'Job {job.id} progress information: {progress_info}')
        
        job.status_message = progress_info
        db.commit()
        db.refresh(job)
        
    job.progress = f'{progress}% complete'
    db.commit()
    db.refresh(job)

    print(f'Job {job.id} progress: {job.progress}')


def parse_json_string(output: str):
    """Validate that the given output is a valid JSON string. 
    Returns the parsed JSON object if valid, otherwise returns None."""

    try:
        # Attempt to parse the string into JSON
        return json.loads(output)
    except (ValueError, TypeError):
        # Return None if parsing fails (invalid JSON or non-string input)
        return None


def convert_time_to_ms(time_str):
    """Converts HH:MM:SS.mmm time format to milliseconds."""
    try:
        hours, minutes, seconds = time_str.split(':')
        seconds, milliseconds = seconds.split('.')
        total_seconds = int(hours) * 3600 + int(minutes) * 60 + int(seconds)
        total_ms = total_seconds * 1000 + int(milliseconds)
        return total_ms
    except ValueError:
        return 0
    
def read_progress_from_pipe(
    db, 
    job, 
    progress_info, 
    process, 
    total_duration
):
    """Reads progress directly from the FFmpeg output pipe and calculates percentage completion."""
    
    for line in iter(process.stdout.readline, ''):
        # Print each line for debugging
        print(line.strip())
        
        # Extract time in HH:MM:SS.mmm format from FFmpeg's output
        time_match = re.search(r'time=(\d{2}:\d{2}:\d{2}\.\d{2})', line)
        if time_match:
            time_str = time_match.group(1)
            print(f"Time found: {time_str}")
            
            # Convert time to milliseconds
            out_time_ms = convert_time_to_ms(time_str)
            
            # Calculate and save the progress
            progress = int((out_time_ms / (total_duration * 1000)) * 100)
            save_and_print_job_progress(db, job, progress, progress_info)
        
        # Check for the end of processing
        if "progress=end" in line:
            print("FFmpeg processing complete.")
            break
        

def run_ffmpeg_with_progress(
    db, 
    job, 
    progress_info, 
    ffmpeg_command, 
    total_duration
):
    """Runs the FFmpeg command with real-time progress reporting."""
    
    # Start FFmpeg with subprocess and capture stderr for progress output
    process = subprocess.Popen(
        ffmpeg_command,
        stderr=subprocess.STDOUT,
        stdout=subprocess.PIPE,
        universal_newlines=True,
    )
    
    # Start a thread to read and process progress from the FFmpeg output
    progress_thread = threading.Thread(
        target=read_progress_from_pipe, 
        args=(db, job, progress_info, process, total_duration)
    )
    progress_thread.start()
    
    # Wait for FFmpeg process and progress thread to complete
    process.wait()
    progress_thread.join()
    print("FFmpeg command and progress thread have completed.")
