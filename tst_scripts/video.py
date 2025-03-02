import ffmpeg


def change_aspect_ratio(input_file, output_file, target_width, target_height):
    """
    Change the aspect ratio of a video by resizing and/or adding padding.
    
    :param input_file: Path to the input video file.
    :param output_file: Path to save the output video file.
    :param target_width: Desired width of the output video.
    :param target_height: Desired height of the output video.
    """
    # Define the scaling and padding filter
    filter_complex = (
        f"scale={target_width}:{target_height}:force_original_aspect_ratio=decrease,"
        f"pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2"
    )

    try:
        # Run the ffmpeg command
        ffmpeg.input(input_file).output(output_file, vf=filter_complex).run(overwrite_output=True)
        print(f"Aspect ratio changed. Output saved to {output_file}")
    except Exception as e:
        print(f"An error occurred: {e}")
        raise e
    

if __name__ == "__main__":
    # change_aspect_ratio('./test-vid.mp4', './test-output.mp4', 1000, 566)
    # Square aspect ratio
    input_video = './test-vid.mp4'
    output_square = './output_square.mp4'
    change_aspect_ratio(input_video, output_square, 1080, 1080)

    # Vertical aspect ratio
    output_vertical = './output_vertical.mp4'
    change_aspect_ratio(input_video, output_vertical, 720, 1280)

    # Horizontal aspect ratio
    output_horizontal = './output_horizontal.mp4'
    change_aspect_ratio(input_video, output_horizontal, 1920, 1080)
