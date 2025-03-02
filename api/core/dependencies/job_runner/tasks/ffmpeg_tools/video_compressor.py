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
compression_speed = payload.get('compression_speed')

# Download video file from minio
save_and_print_job_progress(db, job, 0, f'Downloading and opening video file from {video_url}')
video_file = minio_service.download_file_from_minio(video_url)

try:
    save_and_print_job_progress(db, job, 40, f'Compressing video')
    # Use ffmpeg to extract audio from the video
    cmd, duration, output_video = ffmpeg_service.compress_video(
        input_video=video_file,
        compression_speed=compression_speed,
    )
    
    run_ffmpeg_with_progress(db, job, 'Compressing video', cmd, duration)

    save_and_print_job_progress(db, job, 100, f'Generating preview and download links for compressed video')
    save_url, download_url = minio_service.upload_to_minio(
        folder_name='video-compressor',
        source_file=output_video,
        destination_file=f'vidcmprs-{uuid4().hex}.mp4',
        content_type=mime_types.VIDEO_MP4
    )

    save_and_print_job_progress(db, job, 100, 'Cleaning up')
    delete_file(output_video)

    save_and_print_job_progress(db, job, 100, 'Generating result')
    result = {
        'preview_url': save_url,
        'download_url': download_url,
    }

    save_and_print_job_progress(db, job, 100)
    print(json.dumps(result))

except ffmpeg.Error as ffmpeg_error:
    raise ffmpeg_error

except Exception as e:
    raise e

finally:
    delete_file(video_file)
