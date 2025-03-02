from api.v1.models.project import ProjectToolsEnum as tools


BASE_DIR = 'api/core/dependencies/job_runner/tasks'
AI_TOOLS_BASE_DIR = f'{BASE_DIR}/ai_tools'
FFMPEG_BASE_DIR = f'{BASE_DIR}/ffmpeg_tools'

# Mapping between script names and their corresponding tools
# This is basically to register task scripts
tool_to_script_mapping = {
    # AI TOOLS
    tools.podcast_summarizer.value: f'{AI_TOOLS_BASE_DIR}/podcast_summarizer.py',
    tools.youtube_video_summarizer.value: f'{AI_TOOLS_BASE_DIR}/youtube_video_summarizer.py',
    tools.pdf_summarizer.value: f'{AI_TOOLS_BASE_DIR}/pdf_summarizer.py',
    tools.article_translator.value: f'{AI_TOOLS_BASE_DIR}/article_translator.py',
    tools.audio_summarizer.value: f'{AI_TOOLS_BASE_DIR}/audio_summarizer.py',
    tools.talking_avatar.value: f'{AI_TOOLS_BASE_DIR}/talking_avatar.py',
    tools.script_to_video.value: f'{AI_TOOLS_BASE_DIR}/script_to_video.py',
    tools.image_to_video.value: f'{AI_TOOLS_BASE_DIR}/image_to_video.py',
    tools.tweet_to_tiktok.value: f'{AI_TOOLS_BASE_DIR}/tweet_to_tiktok.py',

    # FFMPEG TOOLS
    tools.audio_extractor.value: f'{FFMPEG_BASE_DIR}/audio_extractor.py',
    tools.resize_video.value: f'{FFMPEG_BASE_DIR}/resize_video.py',
    tools.video_compressor.value: f'{FFMPEG_BASE_DIR}/video_compressor.py',
    tools.gif_creator.value: f'{FFMPEG_BASE_DIR}/gif_creator.py',
    tools.video_watermarker.value: f'{FFMPEG_BASE_DIR}/video_watermarker.py',

    # TESTING
    'Test Job': f'{BASE_DIR}/test_job.py',  # for debugging purposes only
}
