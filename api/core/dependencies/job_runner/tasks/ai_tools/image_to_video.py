import sys, json, os
from uuid import uuid4
from api.utils.files import delete_file
from api.v1.models.job import JobStatus
from api.v1.services.tools.general import general_service
from api.v1.services.tools.talking_avatar import talking_avatar_service
from api.v1.services.tools.general_video_service import video_service
from api.db.database import get_db
from api.utils.minio_service import minio_service
from api.utils.settings import settings
from api.utils import mime_types
from api.v1.services.job import tifi_job_service
from api.core.dependencies.job_runner.app.utils import save_and_print_job_progress

db = next(get_db())

payload = json.loads(sys.argv[1])

job_id = payload.get('job_id', None)
job = tifi_job_service.fetch(db, job_id)

save_and_print_job_progress(db, job, 0, 'Job started')

image_url = payload.get('image_url')
audio_url = payload.get('audio_url', None)


# Download image and audio files from minio
save_and_print_job_progress(db, job, 10, f'Downloading and opening image file from {image_url}')
image_file = minio_service.download_file_from_minio(image_url)

audio_file = None
if audio_url:
    save_and_print_job_progress(db, job, 15, f'Downloading and opening audio file from {audio_url}')
    audio_file = minio_service.download_file_from_minio(audio_url)

# Set up variables
image_file=image_file
aspect_ratio=payload.get('aspect_ratio')
script=payload.get('script')
voice_over=payload.get('voice_over')
audio_file=audio_file


try:
    save_and_print_job_progress(db, job, 20, 'Generating audio from script')
    audio = video_service.convert_text_to_speech(script=script, voice_over=voice_over)

    save_and_print_job_progress(db, job, 30, 'Generating talking avatar video')
    url = talking_avatar_service.generate_talking_avatar_video(image_file, audio)

    save_and_print_job_progress(db, job, 45, 'Downloading and saving generated video')
    # Download video file to the current directory
    initial_save_path = general_service.download_file(
        url=url,
        extension='mp4',
        prefix_file_name='video'
    )
    # video_service.download_file(url, initial_save_path)

    if audio_file:
        save_and_print_job_progress(db, job, 60, 'Applying background audio')
        video_audio_path = os.path.join(settings.TEMP_DIR, f'video-{str(uuid4().hex)}.mp4')
        # Add background audio to the file
        video_service.add_background_audio(
            video_path=initial_save_path,
            audio_path=audio_file,
            output_path=video_audio_path,
        )

    video_dir = os.path.join(settings.STORAGE_DIR, 'video')
    os.makedirs(video_dir, exist_ok=True)
    final_save_path = os.path.join(video_dir, f'video-{str(uuid4().hex)}.mp4')

    save_and_print_job_progress(db, job, 65, 'Changing aspect ratio')
    # Perform aspect ratio resizing based on user input
    video_service.change_aspect_ratio(
        input_file=video_audio_path if audio_file else initial_save_path,
        output_file=final_save_path,
        aspect_ratio=aspect_ratio
    )

    save_and_print_job_progress(db, job, 70, 'Cleaning up temporary files')
    # Delete the temporary audio and video file after processing is done
    if audio_file:
        delete_file(video_audio_path)
    delete_file(initial_save_path)
    delete_file(audio)

    save_and_print_job_progress(db, job, 75, 'Generating video preview link')
    minio_save_file = f'tavtr-{str(uuid4().hex)}.mp4'
    save_url, download_url = minio_service.upload_to_minio(
        folder_name='talking-avatar',
        source_file=final_save_path,
        destination_file=minio_save_file,
        content_type=mime_types.VIDEO_MP4
    )

    save_and_print_job_progress(db, job, 80, 'Generating different video quality download links')
    # Compress video and save to minio as well
    low_quality = video_service.compress_video(input_file=final_save_path, bitrate=500)
    low_quality_vid_preview, low_quality_vid_download = minio_service.upload_to_minio(
        folder_name='talking-avatar',
        source_file=low_quality,
        destination_file=f'tavtr-{str(uuid4().hex)}.mp4',
        content_type=mime_types.VIDEO_MP4
    )
    medium_quality = video_service.compress_video(input_file=final_save_path, bitrate=1080)
    medium_quality_vid_preview, medium_quality_vid_download = minio_service.upload_to_minio(
        folder_name='talking-avatar',
        source_file=medium_quality,
        destination_file=f'tavtr-{str(uuid4().hex)}.mp4',
        content_type=mime_types.VIDEO_MP4
    )

    save_and_print_job_progress(db, job, 85, 'Final cleanup and generating result')
    delete_file(medium_quality)
    delete_file(low_quality)
    delete_file(final_save_path)
    

    save_and_print_job_progress(db, job, 90, 'Gnerating result')
    result = {
        'app_url': save_url,
        'source': url,
        'quality': {
            "low_quality": low_quality_vid_download,
            "medium_quality": medium_quality_vid_download,
            "high_quality": download_url,
        }
    }

    save_and_print_job_progress(db, job, 95)

    print(json.dumps(result))

except Exception as e:
    raise e

finally:
    delete_file(image_file)
    if audio_file:
        delete_file(audio_file)
        