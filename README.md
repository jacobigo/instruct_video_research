# AI Course Video Generator

This project automatically creates narrated course videos from AI-generated **slides** and **scripts**.

Given:
-  A **Markdown** speaking script (`.md`)
-  A **LaTeX/PDF** slide deck (`.tex` → `.pdf`)

it produces:
- Extracted slide images
- Cleaned frame-by-frame narration text
- Natural voice audio (gTTS or OpenAI TTS)
- A fully composed video with slides + synced narration

---
## Technologies Used
- gTTS (moving toward OpenAI TTS in the future)
- pymupdf (splitting slide frames)
- MoviePy (for combining image and audio)
- FFmpeg (for clip concatenation)
- Regex (for complex parsing)
