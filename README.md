# AI Course Video Generator

### Research for:

#### "From Course Concept to Lecture Video: An AI-Powered System for Automated MOOC Development"

### Authors: 
Jacob Igo1, Huaiyuan Yao1, Wanpeng Xu1, Nadia Kellam1, Hua Wei1
1

### Data Mining and Reinforcement Learning (DaRL Lab)

Arizona State University, Tempe, AZ, USA

#### Emails: 
{jigo2, huaiyuan, wanpeng.xu, nadia.kellam, hua.wei}@asu.edu

Submitted and presented at ASU's LERN 2026 convening.

[Download/View](From Course Concept to Lecture Video_ An AI-Powered System for Automated MOOC Development.pdf)

Built off of the foundational research paper:
#### Instructional Agents: LLM Agents on Automated Course Material Generation for Teaching Faculties

link here: https://arxiv.org/abs/2508.19611


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
