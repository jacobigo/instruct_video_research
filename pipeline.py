import functions
import parsing
import re
import pymupdf
from gtts import gTTS
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips
import os
import time
import json
from datetime import datetime


# please use slides path as .pdf and script as .md 
def pipeline(script_path, slides_path, slides_output_folder, audio_output_folder, clip_output_folder, final_video_folder, final_video_name):

    #start logging
    start_time = time.time()
    pipeline_start = datetime.now()

    timing_log = {
        "pipeline_start": pipeline_start.isoformat(),
        "script_path": script_path,
        "slides_path": slides_path,
        "steps": {}
    }

    
    #checking if folders exists, creating them if not
    folders_to_create = [slides_output_folder, audio_output_folder, clip_output_folder, final_video_folder]
    
    for folder in folders_to_create:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f"Created folder: {folder}")
        else:
            print(f"Folder already exists: {folder}")


    step_start = time.time()
    text = parsing.parse_script_file(script_path)
    flattened = []
    for section in text:
        flattened.extend(section['frames'])

    timing_log["steps"]["parse_script"] = time.time() - step_start

    print(f"Parsed script from {script_path}")
    print(f"Total frames detected: {len(flattened)}")


    step_start = time.time()
    slides = functions.extract_slides(slides_path, slides_output_folder)

    timing_log["steps"]["extract_slides"] = time.time() - step_start

    print(f"Converted slides from {slides_path} to images located in {slides_output_folder}")

    
    step_start = time.time()
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

    timing_log["steps"]["generate_clips"] = time.time() - step_start

    print(f"{counter} clips made, located in {clip_output_folder}")

    step_start = time.time()

    #concatenation of clips
    functions.concat_clips(clip_output_folder, final_video_folder, final_video_name)

    timing_log["steps"]["concat_clips"] = time.time() - step_start

    print(f"final video made, located in {final_video_folder}")

    #update final log times for each operation
    end_time = time.time()
    total_duration = end_time - start_time
    timing_log.update({
        "pipeline_end": datetime.now().isoformat(),
        "total_duration_seconds": round(total_duration, 2),
        "total_duration_formatted": f"{int(total_duration // 60)}m {int(total_duration % 60)}s",
        "frames_processed": counter,
        "slides_processed": len(os.listdir(slides_output_folder))
    })

    #write log times to JSON
    log_filename = f"pipeline_timing_{final_video_name}.json"
    with open(log_filename, 'w', encoding='utf-8') as f:
        json.dump(timing_log, f, indent=2, ensure_ascii=False)
    
    print(f"\nPipeline completed in {timing_log['total_duration_formatted']}")
    print(f"Timing log saved to: {log_filename}")
    


if __name__ == '__main__':
    SCRIPT_PATH = 'content_ch1s/intro_to_ai/script.md'
    SLIDES_PATH = 'content_ch1s/intro_to_ai/slides.pdf'
    SLIDES_OUTPUT_FOLDER = 'slide_images'
    AUDIO_OUTPUT_FOLDER = 'audio_files'
    CLIP_OUTPUT_FOLDER = 'audio_image_clips'
    FINAL_VIDEO_OUTPUT_FOLDER = 'final_video'
    FINAL_VIDEO_NAME = 'AI'
    
    pipeline(SCRIPT_PATH, SLIDES_PATH, SLIDES_OUTPUT_FOLDER, AUDIO_OUTPUT_FOLDER, CLIP_OUTPUT_FOLDER, FINAL_VIDEO_OUTPUT_FOLDER, FINAL_VIDEO_NAME)


