# import ffmpeg

# def add_background_audio(video_path: str, audio_path: str, output_path: str, video_audio_volume: float = 1.0):
#     try:
#         # Load the video file with its audio
#         video = ffmpeg.input(video_path)

#         # Load the background audio and adjust its volume
#         background_audio = ffmpeg.input(audio_path).filter('volume', 0.2)

#         # Adjust the volume of the original audio from the video
#         original_audio = video.audio.filter('volume', video_audio_volume)

#         # Combine the original audio with the background audio
#         combined_audio = ffmpeg.filter_([original_audio, background_audio], 'amix', inputs=2)

#         # Combine the video with the combined audio
#         output = ffmpeg.output(
#             video.video,                  # Video stream
#             combined_audio,               # Combined audio stream
#             output_path,                  # Output file path
#             vcodec='copy',                # Copy the video codec (no re-encoding)
#             acodec='aac',                 # Encode the audio with AAC codec
#             strict='experimental',        # Allow use of experimental codecs
#             shortest=None                 # Stop the output when the shortest input ends
#         )

#         # Run the ffmpeg command
#         ffmpeg.run(output, overwrite_output=True)

#         print(f"Successfully added background audio to {output_path}")

#     except ffmpeg.Error as e:
#         print(f"Error occurred: {e.stderr.decode()}")

# # Usage
# video_path = './scripts/test-vid.mp4'
# audio_path = './scripts/test-audio.mp3'
# output_path = './test-output.mp4'

# add_background_audio(video_path, audio_path, output_path)



# # python3 api/core/dependencies/jobs/tasks/talking_avatar.py '{"image_file": "presets/avatars/avatar-32d49deff3.png", "audio_file": null, "aspect_ratio": "square", "script": "I am just testing please. Just work abeg. Let us see what happens from here on out", "voice_over": "man"}'



# from api.utils.minio_service import minio_service

# minio_service.download_file_from_minio(
#     'https://media.tifi.tv/text-to-video/ttvid-02b81068-c5c2-4b38-b540-4f68f22576b2.mp4',
# )

# from api.v1.services.tools.youtube_video_summarizer import ytvid_service

# transcript = ytvid_service.transcribe_audio('./scripts/audio-33f13549-6781-49d0-8dba-cfc284ab0d32.wav')
# transcript_with_timestamp = ytvid_service.generate_transcript_with_timestamp('./scripts/audio-33f13549-6781-49d0-8dba-cfc284ab0d32.wav')
# print(transcript)
# print(transcript_with_timestamp)
# print(ytvid_service.summarize_transcript(transcript))


# import yt_dlp, requests, os

# def get_audio_stream(youtube_url):
#     ydl_opts = {
#         'format': 'bestaudio/best',
#         'noplaylist': True,
#         'quiet': True,
#         'outtmpl': '-',
#         'extractaudio': True,
#         'audioformat': 'mp3',
#         'postprocessors': [{
#             'key': 'FFmpegExtractAudio',
#             'preferredcodec': 'mp3',
#             'preferredquality': '192',
#         }],
#         'no_warnings': True
#     }

#     with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#         info_dict = ydl.extract_info(youtube_url, download=False)
#         audio_url = info_dict['url']
#         try:
#             response = requests.get(audio_url, stream=True)
#             response.raise_for_status()  # Check for errors in the response
            
#             file_path = os.path.join(f'ytaud.mp3')
#             with open(file_path, "wb") as file:
#                 for chunk in response.iter_content(chunk_size=8192):
#                     file.write(chunk)

#             return file_path

#         except requests.RequestException as e:
#             raise e

# # Example usage
# audio_url = get_audio_stream("https://www.youtube.com/watch?v=NHqEFZ9zZuA")
# print("Audio Stream URL:", audio_url)

# {
#   "links": [
#     "https://www.youtube.com/watch?v=BTeuI6j_66c", "https://www.youtube.com/watch?v=NHqEFZ9zZuA", "https://www.youtube.com/watch?v=58Zi8K-2frc"
#   ]
# }

import requests, json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:130.0) Gecko/20100101 Firefox/130.0',
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://cobalt.tools/",
    "Content-Type": "application/json",
    "Origin": "https://cobalt.tools",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "Priority": "u=4"
}
data = {
    "url": "https://www.youtube.com/watch?v=BTeuI6j_66c"
}
response = requests.post(
    'https://api.cobalt.tools/', 
    headers=headers, 
    data=json.dumps(data)
)

print(response.text)