import sys, json, os, requests
from uuid import uuid4

from api.utils.files import delete_file
from api.v1.services.tools.general import general_service
from api.v1.services.tools.talking_avatar import talking_avatar_service
from api.v1.services.tools.general_video_service import video_service
from api.db.database import get_db
from api.utils.minio_service import minio_service
from api.utils.replicate_service import replicate_service
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
bg_audio_url = payload.get('audio_url')

# Download image and audio files from minio
# save_and_print_job_progress(db, job, 10, f'Downloading and opening image file from {image_url}')
# image_file = minio_service.download_file_from_minio(image_url)

bg_audio_file = None
if bg_audio_url:
    save_and_print_job_progress(db, job, 15, f'Downloading and opening audio file from {bg_audio_url}')
    bg_audio_file = minio_service.download_file_from_minio(bg_audio_url)

# Set up variables
# image_file=image_file
width=payload.get('width')
height=payload.get('height')
script=payload.get('script')
voice_url=payload.get('voice_url')
avatar_setting=payload.get('avatar_setting')
# avatar_size=payload.get('avatar_size')
bg_audio_file=bg_audio_file
inpaint_image_url=None

try:
    save_and_print_job_progress(db, job, 20, 'Generating audio from script')
    audio_url = replicate_service.convert_text_to_speech(text=script, sample_audio_file=voice_url)

    if avatar_setting:
        save_and_print_job_progress(db, job, 30, 'Generating inpaint image')
        inpaint_image_url = replicate_service.generate_inpaint_image(image_url, avatar_setting)
    
    save_and_print_job_progress(db, job, 40, 'Generating talking avatar video')
    url = replicate_service.generate_talking_avatar(
        image_url=inpaint_image_url if inpaint_image_url else image_url, 
        audio_url=audio_url,
        generate_full=True if inpaint_image_url else False
    )

    save_and_print_job_progress(db, job, 55, 'Downloading and saving generated video')
    # Download video file to the current directory
    initial_save_path = general_service.download_file(
        url=url,
        extension='mp4',
        prefix_file_name='video'
    )

    if bg_audio_file:
        save_and_print_job_progress(db, job, 60, 'Applying background audio')
        # Add background audio to the file
        video_audio_path = video_service.add_background_audio(
            video_path=initial_save_path,
            audio_path=bg_audio_file
        )

    save_and_print_job_progress(db, job, 65, 'Changing aspect ratio')
    # Perform aspect ratio resizing based on user input
    final_save_path = video_service.change_aspect_ratio(
        input_file=video_audio_path if bg_audio_file else initial_save_path,
        width=width,
        height=height
    )

    save_and_print_job_progress(db, job, 75, 'Cleaning up temporary files')
    # Delete the temporary audio and video file after processing is done
    if bg_audio_file:
        delete_file(video_audio_path)
    delete_file(initial_save_path)
    
    # delete_file(audio)

    save_and_print_job_progress(db, job, 85, 'Generating video preview link')
    minio_save_file = f'tavtr-{str(uuid4().hex)}.mp4'
    preview_url, download_url = minio_service.upload_to_minio(
        folder_name='talking-avatar',
        source_file=final_save_path,
        destination_file=minio_save_file,
        content_type=mime_types.VIDEO_MP4
    )

    delete_file(final_save_path)

    result = {
        'preview': preview_url,
        'download': download_url
    }

    save_and_print_job_progress(db, job, 95)

    print(json.dumps(result))

except Exception as e:
    raise e
    
finally:
    # delete_file(image_file)
    if bg_audio_file:
        delete_file(bg_audio_file)
