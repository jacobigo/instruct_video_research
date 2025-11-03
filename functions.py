import re
import pymupdf
from gtts import gTTS
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips



#clean the meta-data
def clean_frame(text):
    # Remove markdown headings and horizontal rules
    text = re.sub(r'#+.*', '', text)
    text = re.sub(r'-{3,}', '', text)
    
    # Remove parenthetical or bracketed directions
    text = re.sub(r'\*\*?\(.*?\)\*\*?', '', text)
    text = re.sub(r'\*.*?\*', '', text)
    text = re.sub(r'\[.*?\]', '', text)
    
    # Remove "meta" sentences often at the start
    text = re.sub(r'^[\s\S]{0,200}?(?:Welcome|Let’s|Now,)', lambda m: m.group(0), text)
    
    # Remove common filler phrases
    text = re.sub(r'Certainly!.*?(?=\n|$)', '', text)
    text = re.sub(r'Here’s.*?(?=\n|$)', '', text)
    text = re.sub(r'This comprehensive script.*?(?=\n|$)', '', text)

    # Remove multiple newlines and trim
    text = re.sub(r'\n{2,}', '\n', text)
    return text.strip()




#getting each frame of the slides based on the script
def parse_script(script_path):
    with open(script_path, 'r', encoding='utf-8') as f:
        text = f.read()

    frames = re.split(r'\*\*\(Click to Frame \d+.*?\)\*\*', text)
    frames = [clean_frame(f) for f in frames]

    frames = [f.strip() for f in frames if len(f.strip()) > 5]
    return frames




#extracting each image from the slides
def extract_slides(slide_path, output_dir="slide_images"):
    doc = pymupdf.open(slide_path)
    paths = []

    for i, page in enumerate(doc):
        pix = page.get_pixmap(dpi=200)
        img_path = f"{output_dir}\\slide_{i+1}.png"
        if not img_path:
            pix.save(img_path)
            paths.append(img_path)

    return paths



#generating voice for each a portion of text (each frame from the script)
def make_audio_gtts(text, output_path):
    tts = gTTS(text)
    tts.save(output_path)



#generate each clip from image + audio
def make_clip(slide_image_path, audio_path, output_dir='test'):
    audio_clip = AudioFileClip(audio_path)
    slide_image_clip = ImageClip(slide_image_path)

    slide_image_clip = slide_image_clip.with_duration(audio_clip.duration)
    
    final_clip = slide_image_clip.with_audio(audio_clip)
    final_clip.write_videofile(f'{output_dir}\\test_audio_image_clip_overview.mp4', fps=24)







if __name__ == '__main__':
    script_path = 'script.md'
    result = parse_script(script_path)
    print(len(result))
    print(result[1])

    overview = result[1]

    #make_audio_gtts(result[0], r"test\audio_clip_result[0].mp3")
    #make_clip(r"slide_images\slide_3.png", r"test\audio_clip_overview.mp3")

    #img_paths = extract_slides('slides.pdf', output_dir='slide_images')
    #print(img_paths)