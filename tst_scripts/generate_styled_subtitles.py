import random, os
from uuid import uuid4
import ffmpeg

def convert_milliseconds_to_centiseconds(timestamp):
    hours, minutes, seconds = timestamp.split(':')
    sec, millis = seconds.split('.')
    # Convert milliseconds to centiseconds
    centis = int(millis) // 10
    return f"{hours}:{minutes}:{sec}.{centis:02d}"


base_font_path = os.path.abspath('presets/fonts')

fonts = {
    'impact': f'{base_font_path}/impact.ttf',
    'comic sans ms': f'{base_font_path}/comic.ttf',
    'ar christy': f'{base_font_path}/ARCHRISTY.ttf',
    'ar carter': f'{base_font_path}/ARCARTER.ttf',
    'ar bonnie': f'{base_font_path}/ARBONNIE.ttf',
    'levenim mt': f'{base_font_path}/lvnm.ttf',
    'segoe script': f'{base_font_path}/segoesc.ttf',
    'segoe print': f'{base_font_path}/segoepr.ttf',
    'segoe print bold': f'{base_font_path}/segoeprb.ttf',
    'bebas neue': f'{base_font_path}/BebasNeue.ttf',
    'montserrat bold': f'{base_font_path}/Montserrat-Bold.ttf',
    'poppins bold': f'{base_font_path}/Poppins-Bold.ttf',
    'lobster': f'{base_font_path}/Lobster-Regular.ttf',
    'oswald': f'{base_font_path}/Oswald-Regular.ttf',
    'raleway': f'{base_font_path}/Raleway-Regular.ttf',
    'anton': f'{base_font_path}/Anton-Regular.ttf',
    'pacifico': f'{base_font_path}/Pacifico-Regular.ttf',
    'roboto bold': f'{base_font_path}/Roboto-Bold.ttf',
    'playfair display': f'{base_font_path}/PlayfairDisplay-Regular.ttf',
    'dancing script': f'{base_font_path}/DancingScript-Regular.ttf',
    'amatic sc': f'{base_font_path}/AmaticSC-Regular.ttf',
    'open sans bold': f'{base_font_path}/OpenSans-Bold.ttf',
    'merriweather bold': f'{base_font_path}/Merriweather-Bold.ttf',
    'bangers': f'{base_font_path}/Bangers-Regular.ttf',
    'caveat': f'{base_font_path}/Caveat-Regular.ttf',
    'fredoka one': f'{base_font_path}/FredokaOne-Regular.ttf',
    'chewy': f'{base_font_path}/Chewy-Regular.ttf',
    'great vibes': f'{base_font_path}/GreatVibes-Regular.ttf',
    'shadows into light': f'{base_font_path}/ShadowsIntoLight-Regular.ttf',
    'archivo': f'{base_font_path}/ArchivoBlack-Regular.ttf'
}


primary_colors = [
    # "&H00FFFFFF",  # White
    "&H00FFFF00",  # Yellow
    "&H00FF00FF",  # Magenta
    "&H00FF0000",  # Red
    "&H0000FF00",  # Green
    "&H000000FF",  # Blue
    "&H00FFA500",  # Orange
    "&H00A52A2A",  # Brown
]


outline_colors = [
    "&H00000000",  # Black
    "&H00FFFFFF",  # White
    "&H00FFFF00",  # Yellow
    "&H0000FF00",  # Green
    "&H000000FF",  # Blue
    "&H00808080",  # Gray
]

shadow_colors = [
    "&H00000000",  # Black
    "&H00808080",  # Gray
    "&H00FFFFFF",  # White
]

background_colors = [
    "&H00000000",  # Black
    "&H00FFFFFF",  # White
    "&H00202020",  # Dark Gray
    "&H00333333",  # Charcoal Gray
    "&H00F5F5DC",  # Beige
    "&H00B0C4DE",  # Light Steel Blue
]

# Select random styles
font_name = random.choice(list(fonts.keys()))
primary_color = random.choice(primary_colors)
outline_color = random.choice(outline_colors)
shadow_color = random.choice(shadow_colors)
background_color = random.choice(background_colors)

video_file = './tst_scripts/results/tiktok_test_vid.mp4'
output_file = './tst_scripts/results/output_video_with_styled_subtitles.mp4'

probe = ffmpeg.probe(video_file)
video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
width = int(video_stream['width'])
height = int(video_stream['height'])

print(width, height)

# .ass subtitle file header
header = f"""[Script Info]
PlayResY: {height}
PlayResX: {width}
WrapStyle: 1

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, BorderStyle, Outline, Shadow, Alignment, Encoding
Style: S00, {font_name}, 70, {primary_color}, {outline_color}, {background_color}, 1, 1, 1, 5, 0

[Fonts]
"""

captions = "00:00.120 --> 00:03.798\nThis pull request modifies the response structure of the specified\n\n00:03.894 --> 00:07.478\nendpoint to dynamically adjust based on the request\n\n00:07.534 --> 00:10.902\nfrom the front end. The change ensures that the data\n\n00:10.966 --> 00:15.686\nreturned is tailored to the specific needs of the frontend, improving efficiency\n\n00:15.758 --> 00:19.606\nand user experience. This change is required to\n\n00:19.638 --> 00:23.582\nensure that the backend can provide responses that are more aligned with\n\n00:23.606 --> 00:27.032\nthe requirements of the front end. It addresses the issue of\n\n00:27.096 --> 00:30.032\nunnecessary data being sent to the front end,\n\n00:30.136 --> 00:34.096\nwhich can lead to performance inefficiencies and a suboptimal user\n\n00:34.128 --> 00:34.200\nexperience."

captions_list = captions.split('\n\n')
caption_timestamps = [caption[0:23] for caption in captions_list if len(caption) == 23]
formatted_subtitles = []
subtitles_file = f'./tst_scripts/subtitles-{uuid4().hex}.ass'

for caption in captions_list:
    single_caption_list = caption.split('\n')
    
    timestamp_list = single_caption_list[0].split('-->')
    text = single_caption_list[-1].upper()
    start = timestamp_list[0].strip()
    end = timestamp_list[1].strip()
    
    start = start if len(start) == 12 else f'00:{start}'
    end = end if len(end) == 12 else f'00:{end}'
    
    if text == '':
        continue
    
    formatted_subtitles.append({
        "start": convert_milliseconds_to_centiseconds(start),
        "end": convert_milliseconds_to_centiseconds(end),
        "text": text
    })

with open(subtitles_file, 'w') as subtitles:
    # Set up file
    for font, path in fonts.items():
        header += f"{font}: {path}\n"
    header+='\n[Events]\nFormat: Start, End, Style, Text\n'
    
    subtitles.write(header)
    
    for subtitle in formatted_subtitles:
        start_time = subtitle['start']
        end_time = subtitle['end']
        text = subtitle['text']
        
        # Format the subtitle with custom styling (e.g., fade-in, shadow, border)
        event_line = f"Dialogue: {start_time},{end_time},S00,{{\\pos({int(width/2)},{int(height/2)+300})}}{text}\n"
        
        # Write the event to the file
        subtitles.write(event_line)
        
(
    ffmpeg
    .input(video_file)
    # .output(output_file, vf=f"scale=1080:1920:(ow-iw)/2:(oh-ih)/2:black,ass={subtitles_file}")
    # .output(output_file, vf=f"scale=1080:1920,ass={subtitles_file}")
    .output(output_file, vf=f"ass={subtitles_file}")
    .run(overwrite_output=True)
)
print(f"Subtitled video saved as {output_file}")


# filter_complex = (
#     f"scale=1080:1920:force_original_aspect_ratio=decrease,"
#     f"pad=1080:1920:(ow-iw)/2:(oh-ih)/2"
# )

# (
#     ffmpeg
#     .input(video_file)
#     .output(output_file, vf=filter_complex)
#     .run(overwrite_output=True)
# )