import sys, json, os
from uuid import uuid4
import ffmpeg

from api.utils.files import delete_file
from api.db.database import get_db
from api.utils.minio_service import minio_service
from api.utils.settings import settings
from api.utils import mime_types
from api.v1.services.job import tifi_job_service
from api.v1.services.tools.ffmpeg_tools import ffmpeg_service
from api.core.dependencies.job_runner.app.utils import run_ffmpeg_with_progress, save_and_print_job_progress

db = next(get_db())

payload = json.loads(sys.argv[1])

job_id = payload.get('job_id', None)
job = tifi_job_service.fetch(db, job_id)

save_and_print_job_progress(db, job, 0, 'Job started')

video_url = payload.get('video_url')
audio_extension = payload.get('audio_extension')
start_time = payload.get('start_time')
end_time = payload.get('end_time')

# Download video file from minio
save_and_print_job_progress(db, job, 0, f'Downloading and opening video file from {video_url}')
video_file = minio_service.download_file_from_minio(video_url)

try:
    # Use ffmpeg to extract audio from the video
    cmd, duration, audio_path = ffmpeg_service.extract_audio_from_video(
        input_video=video_file,
        audio_extension=audio_extension,
        start_time=start_time,
        end_time=end_time
    )
    
    # Run ffmpeg command
    run_ffmpeg_with_progress(db, job, 'Extracting audio from video', cmd, duration)

    save_and_print_job_progress(db, job, 100, f'Generating preview and download links for generated audio')
    
    mime_type = mime_types.AUDIO_MP3 if audio_extension == 'mp3' else mime_types.AUDIO_WAV
    save_url, download_url = minio_service.upload_to_minio(
        folder_name='audio-extractor',
        source_file=audio_path,
        destination_file=f'audioextr-{uuid4().hex}.{audio_extension}',
        content_type=mime_type
    )

    # save_and_print_job_progress(db, job, 80, 'Cleaning up')
    save_and_print_job_progress(db, job, 100, 'Cleaning up')
    delete_file(audio_path)

    # save_and_print_job_progress(db, job, 90, 'Generating result')
    save_and_print_job_progress(db, job, 100, 'Generating result')
    result = {
        'preview_url': save_url,
        'download_url': download_url,
    }

    # save_and_print_job_progress(db, job, 95)
    save_and_print_job_progress(db, job, 100)
    print(json.dumps(result))

except ffmpeg.Error as ffmpeg_error:
    raise ffmpeg_error

except Exception as e:
    raise e

finally:
    if video_file:
        delete_file(video_file)
