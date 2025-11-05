import functions
import parsing
import re
import pymupdf
from gtts import gTTS
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips
import os


# please use slides path as .pdf and script as .md 
def pipeline(script_path, slides_path, slides_output_folder, audio_output_folder, clip_output_folder, final_video_folder):

    text = parsing.parse_script_file(script_path)
    flattened = []
    for section in text:
        flattened.extend(section['frames'])

    print(f"Parsed script from {script_path}")
    print(f"Total frames detected: {len(flattened)}")

    slides = functions.extract_slides(slides_path, slides_output_folder)
    print(f"Converted slides from {slides_path} to images located in {slides_output_folder}")

    
    counter = 0
    for filename in os.listdir(slides_output_folder):

        if counter >= len(flattened):
            print(f"Warning: More slides ({len(os.listdir(slides_output_folder))}) than script frames ({len(text)})")
            break

        slide_image_path = os.path.join(slides_output_folder, filename)
        audio_output_path = os.path.join(audio_output_folder, f"audio_file_{counter}.mp3")
        clip_output_path = os.path.join(clip_output_folder, f"clip_file_{counter}.mp4")
        functions.make_audio_gtts(flattened[counter], audio_output_path)
        print(f"audio output file: {audio_output_path}\n")
        print(f"slide output file: {slide_image_path}\n")
        functions.make_clip(slide_image_path, audio_output_path, clip_output_path)
        counter += 1

    print(f"{counter} clips made, located in {clip_output_folder}")

    functions.concat_clips(clip_output_folder, final_video_folder)

    print(f"final video made, located in {final_video_folder}")


if __name__ == '__main__':
    SCRIPT_PATH = 'script.md'
    SLIDES_PATH = 'slides.pdf'
    SLIDES_OUTPUT_FOLDER = 'slide_images'
    AUDIO_OUTPUT_FOLDER = 'audio_files'
    CLIP_OUTPUT_FOLDER = 'audio_image_clips'
    FINAL_VIDEO_OUTPUT_FOLDER = 'final_video'
    
    pipeline(SCRIPT_PATH, SLIDES_PATH, SLIDES_OUTPUT_FOLDER, AUDIO_OUTPUT_FOLDER, CLIP_OUTPUT_FOLDER, FINAL_VIDEO_OUTPUT_FOLDER)


