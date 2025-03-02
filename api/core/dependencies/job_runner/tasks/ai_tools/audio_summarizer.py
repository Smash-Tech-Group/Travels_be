import json, sys
from uuid import uuid4

from api.utils.files import delete_file
from api.v1.services.tools.audio_summarizer import audio_summary_service
from api.v1.services.tools.pdf_summarizer import pdf_summary_service
from api.utils import mime_types
from api.db.database import get_db
from api.utils.minio_service import minio_service
from api.v1.services.job import tifi_job_service
from api.core.dependencies.job_runner.app.utils import save_and_print_job_progress

db = next(get_db())

payload = json.loads(sys.argv[1])

job_id = payload.get('job_id', None)
job = tifi_job_service.fetch(db, job_id)

save_and_print_job_progress(db, job, 0, 'Job started')

audio_url = payload.get('audio_url')
detail_level = payload.get('detail_level')

save_and_print_job_progress(db, job, 10, f'Downloading and opening audio file from {audio_url}')
audio_file = minio_service.download_file_from_minio(audio_url)

try:
    save_and_print_job_progress(db, job, 30, 'Transcribing audio')
    transcript = audio_summary_service.transcribe_audio(audio_file)
        
    save_and_print_job_progress(db, job, 45, 'Summarizing transcript')
    transcript_summary = audio_summary_service.summarize_transcript(transcript, detail_level=detail_level)

    save_and_print_job_progress(db, job, 55, 'Generating transcript with timestamp')
    transcript_with_timestamp = audio_summary_service.generate_transcript_with_timestamp(audio_file)
    
    save_and_print_job_progress(db, job, 65, 'Saving to PDF')
    pdf_file = audio_summary_service.save_to_pdf(
        transcript=transcript_with_timestamp,
        summary=transcript_summary,
    )

    save_and_print_job_progress(db, job, 75, 'Uploading PDF file for storage')
    save_url, download_url = minio_service.upload_to_minio(
        folder_name="audio-summary",
        source_file=pdf_file,
        destination_file=f"podsum-{str(uuid4().hex)}.pdf",
        content_type=mime_types.APPLICATION_PDF,
    )

    save_and_print_job_progress(db, job, 85, 'Making calculations')
    # Calculate summary read time
    summary_read_time = pdf_summary_service.get_reading_time(transcript_summary)
    estimated_summary_read_time = f'{summary_read_time} minute' if summary_read_time == 1 else f'{summary_read_time} minutes'

    save_and_print_job_progress(db, job, 90, 'Cleaning up')
    delete_file(pdf_file)

    save_and_print_job_progress(db, job, 95, 'Fetching result')
    result = json.dumps({
        "summary": transcript_summary,
        "transcript": transcript_with_timestamp,
        "estimated_read_time": estimated_summary_read_time,
        "preview_utl": save_url,
        "download_url": download_url,
    })

    print(result)

except Exception as e:
    raise e

finally:
    delete_file(audio_file)