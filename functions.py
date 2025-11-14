import re
import pymupdf
from gtts import gTTS
from moviepy import ImageClip, AudioFileClip, VideoFileClip, concatenate_videoclips
import os
import subprocess
import parsing
from openai import OpenAI


#extracting each image from the slides
def extract_slides(slide_path, output_dir="slide_images", skip_first=True):
    doc = pymupdf.open(slide_path)
    paths = []


    start_index = 1 if skip_first else 0
    for i, page in enumerate(doc):
        if i < start_index:
            continue
        pix = page.get_pixmap(dpi=200)
        slide_num = i + 1
        if slide_num <= 10:
            img_path = f"{output_dir}\\slide_0{i}.png"
        else:
            img_path = f"{output_dir}\\slide_{i}.png"
        if not os.path.exists(img_path):
            pix.save(img_path)
        paths.append(img_path)

    return paths



#generating voice for each a portion of text (each frame from the script)
def make_audio_gtts(text, output_path):
    tts = gTTS(text)
    tts.save(output_path)


#experimental, for future use
def make_audio_openai(text, output_path, voice="alloy", model="tts-1"):
    """
    Generate audio using OpenAI TTS API
    
    Args:
        text (str): Text to convert to speech
        output_path (str): Path where audio file will be saved
        voice (str): Voice to use - options: alloy, echo, fable, onyx, nova, shimmer
        model (str): Model to use - options: tts-1 (faster), tts-1-hd (higher quality)
    """
    client = OpenAI()  # Make sure OPENAI_API_KEY is set in environment variables
    
    with client.audio.speech.with_streaming_response.create(
        model=model,
        voice=voice,
        input=text,
    ) as response:
        response.stream_to_file(output_path)



#generate each clip from image + audio
def make_clip(slide_image_path, audio_path, output_dir):
    audio_clip = AudioFileClip(audio_path)
    slide_image_clip = ImageClip(slide_image_path)

    slide_image_clip = slide_image_clip.with_duration(audio_clip.duration)
    
    final_clip = slide_image_clip.with_audio(audio_clip)
    final_clip.write_videofile(output_dir, fps=24)


#using ffmpeg instead of moviepy for faster performance
def concat_clips(clip_folder, final_video_folder, final_video_name):

    clip_list = []
    for clip in os.listdir(clip_folder):
        clip_path = os.path.join(clip_folder, clip)
        clip_list.append(clip_path)

    #clip_list.sort()
    def natural_sort_key(s):
        return [int(text) if text.isdigit() else text.lower() for text in re.split (r'(\d+)', s)]
    
    clip_list.sort(key=natural_sort_key)

    concat_file = os.path.join(clip_folder, 'concat_list.txt')
    with open(concat_file, 'w') as f:
        for clip in clip_list:
            #absolute path for ffmpeg
            abs_path = os.path.abspath(clip).replace('\\', '/')
            f.write(f"file '{abs_path}'\n")

    #os.makedirs(final_video_folder, exist_ok=True)
    output_path = f"{final_video_folder}\\final_video_{final_video_name}.mp4"

    subprocess.run([
        'ffmpeg', '-f', 'concat', '-safe', '0',
        '-i', concat_file,
        '-c', 'copy',  # Copy streams without re-encoding
        output_path
    ])    

    os.remove(concat_file)





#testing
if __name__ == '__main__':
    script_path = 'script.md'

    #make_audio_gtts(result[0], r"test\audio_clip_result[0].mp3")
    #make_clip(r"slide_images\slide_3.png", r"test\audio_clip_overview.mp3")

    #img_paths = extract_slides('slides.pdf', output_dir='slide_images')
    #print(img_paths)

    #concat_clips('audio_image_clips', 'final_video')