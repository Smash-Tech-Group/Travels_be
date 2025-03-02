import sys, json, os
from uuid import uuid4

from api.utils.files import delete_file
from api.v1.services.tools.general_video_service import video_service
from api.v1.services.tools.general import general_service
from api.v1.services.tools.tweet_to_tiktok import tweet_to_tiktok_service
from api.v1.services.tools.talking_avatar import talking_avatar_service
from api.db.database import get_db
from api.utils.minio_service import minio_service
from api.utils.settings import settings
from api.utils.replicate_service import replicate_service
from api.utils import mime_types
from api.v1.services.job import tifi_job_service
from api.core.dependencies.job_runner.app.utils import save_and_print_job_progress


db = next(get_db())

payload = json.loads(sys.argv[1])

job_id = payload.get('job_id', None)
job = tifi_job_service.fetch(db, job_id)

save_and_print_job_progress(db, job, 0, 'Job started')

audio_url = payload.get('bg_audio_url', None)

background_audio = None
if audio_url:
    save_and_print_job_progress(db, job, 10, f'Downloading and opening audio file from {audio_url}')
    background_audio = minio_service.download_file_from_minio(audio_url)


script = payload.get('text')
media_urls = payload.get('scene_media_urls')
video_style = payload.get('video_style')
voice_url = payload.get('voice_url')
avatar_image_url = payload.get('avatar_image_url')
width = payload.get('width')
height = payload.get('height')
avatar_setting = payload.get('avatar_setting')

audio_file = None

try:
    # if video_style == 'talking avatar':
    # if avatar_image_url:
    save_and_print_job_progress(db, job, 15, 'Generating audio from script')
    audio_file, audio_url = tweet_to_tiktok_service.generate_audio(script, voice_url)
    # audio_file = os.path.join('tst_scripts', 'results', 'testing.wav')
    
    save_and_print_job_progress(db, job, 25, 'Downloading media files')
    media_files = tweet_to_tiktok_service.download_media(media_urls)
    
    # save_and_print_job_progress(db, job, 15, 'Converting text to speech')
    # audio_url = replicate_service.convert_text_to_speech(text=script, sample_audio_file=voice_url)
    
    save_and_print_job_progress(db, job, 35, 'Generating inpaint avatar image')
    avatar_url = replicate_service.generate_inpaint_image(avatar_image_url, avatar_setting)[0]
    
    save_and_print_job_progress(db, job, 45, 'Generating talking avatar video')
    video_url = replicate_service.generate_talking_avatar(avatar_url, audio_url, generate_full=True)
    # video_url = replicate_service.generate_talking_avatar(avatar_url, audio_url)
    # video_url = replicate_service.generate_talking_avatar(avatar_image_url, audio_url)
    
    save_and_print_job_progress(db, job, 55, 'Saving talking avatar video')
    avatar_video_file = general_service.download_file(video_url, 'mp4', 'video')

    # save_and_print_job_progress(db, job, 45, 'Downloading and saving generated video')
    # # Download video file to the current directory
    # video_file = general_service.download_file(
    #     url=video_url,
    #     extension='mp4',
    #     prefix_file_name='video'
    # )
        
    # else:
    # save_and_print_job_progress(db, job, 15, 'Generating audio from script')
    # audio_file = tweet_to_tiktok_service.generate_audio(script, voice_url)
    # # audio_file = os.path.join('tst_scripts', 'results', 'testing.wav')
    
    # save_and_print_job_progress(db, job, 25, 'Downloading media files')
    # media_files = tweet_to_tiktok_service.download_media(media_urls)

    save_and_print_job_progress(db, job, 60, 'Composing video with media files')
    video_file = tweet_to_tiktok_service.compose_video(
        base_video_file=avatar_video_file,
        audio_file=audio_file, 
        overlay_media_files=media_files,
        width=width,
        height=height,
        # interval=5,
        # overlay_duration=3
        num_overlays=3
    )

    save_and_print_job_progress(db, job, 70, 'Generating subtitle file from generated audio')
    subtitles_file = tweet_to_tiktok_service.generate_subtitles(audio_file, width, height)
    
    save_and_print_job_progress(db, job, 80, 'Embedding subtitles in generated video')
    video_with_subtitles = tweet_to_tiktok_service.add_subtitles_to_video(subtitles_file, video_file)

    if background_audio:
        save_and_print_job_progress(db, job, 85, 'Applying background music to the video')
        # Add background music to video
        video_with_audio = video_service.add_background_audio(
            video_path=video_with_subtitles, 
            audio_path=background_audio, 
        )

    save_and_print_job_progress(db, job, 90, 'Cleaning up')
    # Delete unnecessary files
    # TODO: Uncomment this
    if audio_file and 'testing' not in audio_file:
        delete_file(audio_file)
    delete_file(subtitles_file)
    delete_file(video_file)
    # delete_file(video_with_subtitles)

    save_and_print_job_progress(db, job, 95, 'Generating preview and download links for generated video')
    minio_save_file = f'twttotiktk-{str(uuid4().hex)}.mp4'
    save_url, download_url = minio_service.upload_to_minio(
        folder_name='tweet-to-tiktok',
        source_file=video_with_subtitles if not background_audio else video_with_audio,
        destination_file=minio_save_file,
        content_type=mime_types.VIDEO_MP4
    )

    save_and_print_job_progress(db, job, 90, 'Generating result and final cleanup')
    result = {
        "url": save_url,
        "download_url": download_url,
    }

    delete_file(video_with_subtitles)
    if background_audio:
        delete_file(video_with_audio)

    save_and_print_job_progress(db, job, 98)

    print(json.dumps(result))

except Exception as e:
    raise e

finally:
    if background_audio:
        delete_file(background_audio)
