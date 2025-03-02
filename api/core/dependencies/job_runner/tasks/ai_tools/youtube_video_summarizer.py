import json, sys, os
from uuid import uuid4

from api.db.database import get_db
from api.v1.services.job import tifi_job_service
from api.utils.files import delete_file
from api.utils.minio_service import minio_service
from api.utils.settings import settings
from api.utils import mime_types
from api.v1.services.tools.youtube_video_summarizer import ytvid_service
from api.core.dependencies.job_runner.app.utils import save_and_print_job_progress

db = next(get_db())

payload = json.loads(sys.argv[1])

job_id = payload.get('job_id', None)
job = tifi_job_service.fetch(db, job_id)

save_and_print_job_progress(db, job, 0, 'Job started')

links = payload.get('links')
batch = payload.get('batch')
vid_type = payload.get('type')
detail_level = payload.get('detail_level')

video_data = {}
videos_list = []  # to store list of dictionaries for every processed video data

# Initialize final result dict
final_result = {}  # for batch upload

number_of_videos_to_process = len(links)
progress_per_video = round(95 / number_of_videos_to_process)

# Set up save path for csv file for batch upload
csv_save_path = os.path.join(settings.TEMP_DIR, f"ytvidsum-{uuid4().hex}.csv")

video_file = None
audio_file = None

try: 
    for id, link in enumerate(links):
        if vid_type == 'youtube':
            if not batch:
                save_and_print_job_progress(db, job, 15, 'Extracting audio stream from youtube video')
            audio_file = ytvid_service.get_audio_stream(link)

            if not batch:
                save_and_print_job_progress(db, job, 35, 'Transcribing audio')
            transcript = ytvid_service.transcribe_audio(audio_file)

        else:
            if not batch:
                save_and_print_job_progress(db, job, 10, 'Downloading video file from minio')
            video_file = minio_service.download_file_from_minio(link)

            if not batch:
                save_and_print_job_progress(db, job, 25, 'Extracting audio from downloaded video')
            # Extract the audio from video downloaded from minio
            audio_file = ytvid_service.extract_audio_from_video(video_file)

            if not batch:
                save_and_print_job_progress(db, job, 35, 'Transcribing audio')
            transcript = ytvid_service.transcribe_audio(audio_file)

        if not batch:
            save_and_print_job_progress(db, job, 45, 'Summarizing transcript')
        transcript_summary = ytvid_service.summarize_transcript(transcript, detail_level=detail_level)

        if not batch:
            save_and_print_job_progress(db, job, 55, 'Generating transcript with timestamp')
        transcript_with_timestamp = ytvid_service.generate_transcript_with_timestamp(audio_file)
        transcript_with_timestamp_srt = ytvid_service.generate_transcript_with_timestamp(audio_file, as_srt=True)

        if not batch:
            save_and_print_job_progress(db, job, 65, 'Saving to PDF')
        pdf_file = ytvid_service.save_transcript_and_summary_to_pdf(
            transcript=transcript_with_timestamp,
            summary=transcript_summary,
        )

        # Update and save csv file
        if batch:
            ytvid_service.save_transcript_and_summary_to_csv(
                transcript=transcript,
                summary=transcript_summary,
                transcript_with_timestamp=transcript_with_timestamp,
                transcript_with_timestamp_srt=transcript_with_timestamp_srt,
                save_path=csv_save_path
            )

        # Upload pdf dummary to minio
        if not batch:
            save_and_print_job_progress(db, job, 75, 'Generating summary PDF preview and download links')
        pdf_preview_url, pdf_download_url = minio_service.upload_to_minio(
            folder_name='youtube-video-summarizer',
            source_file=pdf_file,
            destination_file=f"ytvidsum-{str(uuid4().hex)}.pdf",
            content_type=mime_types.APPLICATION_PDF,
        )
    
        if not batch:
            save_and_print_job_progress(db, job, 90, 'Cleaning up')
        delete_file(pdf_file)

        if not batch:
            save_and_print_job_progress(db, job, 95, 'Generating result')

        video_data = {
            "summary": transcript_summary,
            "summary_word_count": len(transcript_summary.split()),
            "transcript": transcript_with_timestamp,
            "transcript_word_count": len(transcript.split()),
            'subtitles': transcript_with_timestamp_srt,
            "preview_url": pdf_preview_url,
            "download_url": pdf_download_url
        }

        if batch:
            videos_list.append(video_data)

            save_and_print_job_progress(
                db, 
                job, 
                progress = (id+1) * progress_per_video, 
                progress_info = f'Video {id+1} of {number_of_videos_to_process} processed'
            )

        if not batch:
            save_and_print_job_progress(db, job, 95)

    
    # Compile final result
    final_result = {'videos': videos_list}
    
    # Generate csv file
    if batch:
        # Upload updated csv file
        csv_preview_url, csv_download_url = minio_service.upload_to_minio(
            folder_name='youtube-video-summarizer',
            source_file=csv_save_path,
            destination_file=f"ytvidsum-{str(uuid4().hex)}.csv",
            content_type=mime_types.TEXT_CSV,
        )
        delete_file(csv_save_path)

        # Add csv file to the result 
        final_result['csv'] = {
            "preview_url": csv_preview_url,
            "download_url": csv_download_url,
        }

    print(json.dumps(final_result if batch else video_data))

except Exception as e:
    raise e

finally:
    if video_file:
        delete_file(video_file)
    if audio_file:
        delete_file(audio_file)
