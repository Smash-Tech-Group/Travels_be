import sys, json, os
from uuid import uuid4

from api.v1.services.tools.script_to_video import ttv_service
from api.utils.files import delete_file
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

audio_url = payload.get('audio_url', None)

background_audio = None
if audio_url:
    save_and_print_job_progress(db, job, 10, f'Downloading and opening audio file from {audio_url}')
    background_audio = minio_service.download_file_from_minio(audio_url)


script=payload.get('script')
scenes=payload.get('scenes')
voice_url=payload.get('voice_url')
width=payload.get('width')
height=payload.get('height')
background_audio=background_audio

try:
    save_and_print_job_progress(db, job, 15, 'Generating audio from script')
    audio_file = video_service.convert_text_to_speech(script, voice_url)

    save_and_print_job_progress(db, job, 25, 'Generating subtitle file from generated audio')
    subtitle_file = video_service.generate_subtitles_from_audio(audio_file)

    save_and_print_job_progress(db, job, 30, 'Generating images for scenes')
    images = ttv_service.generate_images_for_scenes(scenes)

    save_and_print_job_progress(db, job, 45, 'Creating video')
    video_file = ttv_service.create_video_with_images(images, audio_file)

    save_and_print_job_progress(db, job, 55, 'Embedding subtitles in generated video')
    # Add subtitles to video
    video_with_subtitles = video_service.add_subtitles_to_video(
        input_video=video_file, 
        subtitles_file=subtitle_file,
    )

    if background_audio:
        save_and_print_job_progress(db, job, 60, 'Applying background music to the video')
        # Add background music to video
        video_with_bg_music_path = os.path.join(settings.TEMP_DIR, f'ttvideo-{str(uuid4().hex)}.mp4')
        video_with_audio = video_service.add_background_audio(
            video_path=video_with_subtitles, 
            audio_path=background_audio, 
            output_path=video_with_bg_music_path
        )

    save_and_print_job_progress(db, job, 75, 'Changing aspect ratio of video')
    # Adjust aspect ratio
    final_result_file = video_service.change_aspect_ratio(
        input_file=video_with_audio if background_audio is not None else video_with_subtitles, 
        width=width,
        height=height
    )

    save_and_print_job_progress(db, job, 80, 'Cleaning up')
    # Delete unnecessary files
    delete_file(audio_file)
    delete_file(subtitle_file)
    delete_file(video_file)
    delete_file(video_with_subtitles)
    if background_audio:
        delete_file(video_with_bg_music_path)
    for img in images:
        delete_file(img)

    # save_url = f'{settings.APP_URL}/{final_result_file}'

    save_and_print_job_progress(db, job, 85, 'Generating preview and download links for generated video')
    minio_save_file = f'scrtovid-{str(uuid4().hex)}.mp4'
    save_url, download_url = minio_service.upload_to_minio(
        folder_name='script-to-video',
        source_file=final_result_file,
        destination_file=minio_save_file,
        content_type=mime_types.VIDEO_MP4
    )

    save_and_print_job_progress(db, job, 90, 'Generating result and final cleanup')
    result = {
        "url": save_url,
        "download_url": download_url,
    }

    delete_file(final_result_file)

    if background_audio:
        delete_file(background_audio)

    save_and_print_job_progress(db, job, 95)

    print(json.dumps(result))

except Exception as e:
    raise e

finally:
    if background_audio:
        delete_file(background_audio)
