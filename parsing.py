import re
import json
from pathlib import Path

# === Helpers ===

def read_file(p):
    return Path(p).read_text(encoding='utf-8')

def clean_text(s):
    """
    Remove markdown headings, parenthetical/italicized directions, and meta text
    while preserving bold emphasis meant to be spoken.
    """
    s = s.replace('\r\n', '\n').strip()

    # Remove markdown headings, separators
    s = re.sub(r'(?m)^\s{0,3}#+\s.*$', '', s)
    s = re.sub(r'(?m)^\s*-{3,}\s*$', '', s)
    s = re.sub(r'(?m)^\s*\*{3,}\s*$', '', s)

    # Remove bolded parentheses or bracketed directions
    s = re.sub(r'\*\*\s*\(.*?\)\s*\*\*', '', s)
    s = re.sub(r'\*\*\s*\[.*?\]\s*\*\*', '', s)

    # Remove single-asterisked or italic directions (non-bold)
    s = re.sub(r'(?<!\*)\*(?!\*)([^*]{0,200}?)(?<!\*)\*(?!\*)', '', s)

    # Remove plain parentheses/brackets that are instructions
    s = re.sub(r'\([^)]{0,120}?\)', '', s)
    s = re.sub(r'\[[^\]]{0,120}?\]', '', s)

    # Remove common instructor/meta phrases (case-insensitive)
    s = re.sub(r'(?i)\b(transitioning from previous slide|wait for questions|instructor notes?:?|slide transition|pause here)\b.*', '', s)

    # Remove "Certainly!" etc.
    s = re.sub(r'(?mi)^\s*certainly!.*$', '', s)
    s = re.sub(r'(?mi)^\s*here\'s a comprehensive speaking script.*$', '', s)
    s = re.sub(r'(?mi)^\s*this comprehensive script should facilitate.*$', '', s)

    # Clean up whitespace
    s = re.sub(r'\n{2,}', '\n\n', s).strip()

    # Replace remaining asterisks with underscores
    s = s.replace('*', '_')

    return s

# === Core parser ===

# Pattern to match frame markers - EXCLUDING "Continued" frames
FRAME_MARKER_PAT = re.compile(
    r'(?:^\s*\*\*\s*\((?:Click to )?Frame\s*\d+(?!.*[Cc]ontinued)[^)]*\)\s*\*\*\s*$|'
    r'^\s*\*\*\s*\[Frame\s*\d+(?!.*[Cc]ontinued)[^\]]*\]\s*\*\*\s*$|'
    r'^\s*\[Frame\s*\d+(?!.*[Cc]ontinued)[^\]]*\]\s*$|'
    r'^\s*\*\*\s*\(Begin[^\)]*\)\s*\*\*\s*$|'
    r'^\s*\*\*\s*\[(?:Move|Advance|Transition)\s+to\s+Frame\s*\d+(?!.*[Cc]ontinued)[^\]]*\]\s*\*\*\s*$)',
    flags=re.I | re.M
)

# Pattern to match "Frame X Continued" markers (to be removed but not used as split points)
FRAME_CONTINUED_PAT = re.compile(
    r'^\s*\*\*\s*\[Frame\s*\d+\s+Continued\]\s*\*\*\s*$',
    flags=re.I | re.M
)

SECTION_HEADER = re.compile(r'(?m)^\s*##\s+Section\s+\d+[:\s].*$', flags=re.I)

FRAMES_COUNT_IN_SECTION = re.compile(r'\*\s*\((\d+)\s+frames\)\s*\*', flags=re.I)

def split_into_sections(text):
    """
    Return list of (section_header_text, section_body_text) tuples.
    If no leading sections, returns one section with header None.
    """
    sections = []
    matches = list(SECTION_HEADER.finditer(text))
    
    if not matches:
        return [(None, text)]
    
    for i, m in enumerate(matches):
        header = m.group(0).strip()
        body_start = m.end()
        
        if i + 1 < len(matches):
            end = matches[i + 1].start()
        else:
            end = len(text)
        
        body = text[body_start:end].strip()
        sections.append((header, body))
    
    return sections

def remove_frame_continued_markers(text):
    """
    Remove 'Frame X Continued' markers from text since they don't denote new frames.
    """
    return FRAME_CONTINUED_PAT.sub('', text)

def extract_frames_from_section(header, body):
    """
    Given a section body, return an ordered list of frame texts (cleaned).
    Uses explicit frame markers and improved heuristics.
    """
    # First, remove "Frame X Continued" markers as they don't split frames
    body = remove_frame_continued_markers(body)
    
    # Try to read declared frame count
    count_match = FRAMES_COUNT_IN_SECTION.search(body)
    declared_count = int(count_match.group(1)) if count_match else None

    # Find all explicit frame marker matches (excluding continued frames)
    markers = list(FRAME_MARKER_PAT.finditer(body))
    
    if markers and len(markers) >= 2:
        # Use frame markers to split
        frames = []
        
        for i in range(len(markers)):
            start = markers[i].end()  # Start after the marker
            
            # Find end point (next marker or end of body)
            if i + 1 < len(markers):
                end = markers[i + 1].start()
            else:
                end = len(body)
            
            chunk = body[start:end].strip()
            
            # Skip empty chunks
            if chunk:
                frames.append(chunk)
        
        # Clean and return
        cleaned_frames = [clean_text(f) for f in frames if f.strip()]
        
        # Verify against declared count if available
        if declared_count and len(cleaned_frames) != declared_count:
            print(f"Warning: Section '{header}' declares {declared_count} frames but found {len(cleaned_frames)} frames")
        
        return cleaned_frames
    
    # No clear frame markers - try splitting by horizontal rules
    hr_pattern = re.compile(r'\n\s*-{3,}\s*\n')
    chunks = [c.strip() for c in hr_pattern.split(body) if c.strip()]
    
    # If we have a declared count and chunks match, use them
    if declared_count and len(chunks) == declared_count:
        return [clean_text(c) for c in chunks]
    
    # Try splitting by double newlines (paragraphs)
    paragraphs = [p.strip() for p in re.split(r'\n\n+', body) if p.strip()]
    
    # Filter out very short paragraphs (likely artifacts)
    paragraphs = [p for p in paragraphs if len(p) > 50]
    
    # If declared count exists, try to group paragraphs
    if declared_count and declared_count > 0:
        if len(paragraphs) >= declared_count:
            return group_paragraphs_evenly(paragraphs, declared_count)
        else:
            # Not enough paragraphs, return what we have
            return [clean_text(p) for p in paragraphs]
    
    # No declared count - treat each substantial paragraph as a frame
    if len(paragraphs) <= 15:  # Reasonable frame limit
        return [clean_text(p) for p in paragraphs]
    
    # Last resort: return whole section as one frame
    return [clean_text(body)]

def group_paragraphs_evenly(paragraphs, target_count):
    """
    Group paragraphs into target_count frames, distributing evenly.
    """
    if target_count <= 0:
        return ['\n\n'.join(paragraphs)]
    
    if len(paragraphs) <= target_count:
        return [clean_text(p) for p in paragraphs]
    
    # Calculate how many paragraphs per frame
    per_frame = len(paragraphs) // target_count
    remainder = len(paragraphs) % target_count
    
    frames = []
    idx = 0
    
    for i in range(target_count):
        # Distribute remainder paragraphs across first few frames
        count = per_frame + (1 if i < remainder else 0)
        frame_paras = paragraphs[idx:idx + count]
        frames.append(clean_text('\n\n'.join(frame_paras)))
        idx += count
    
    return frames

# === Main entry ===

def parse_script_file(md_path, out_json='parsed_frames.json'):
    text = read_file(md_path)
    sections = split_into_sections(text)

    parsed = []
    total_frames = 0
    
    for header, body in sections:
        frames = extract_frames_from_section(header, body)
        total_frames += len(frames)
        parsed.append({
            'section_header': header,
            'num_frames_detected': len(frames),
            'frames': frames
        })

    # Save JSON
    Path(out_json).write_text(json.dumps(parsed, indent=2, ensure_ascii=False), encoding='utf-8')
    
    print(f'\nTotal sections: {len(parsed)}')
    print(f'Total frames: {total_frames}')
    
    return parsed

if __name__ == '__main__':
    import sys
    md = sys.argv[1] if len(sys.argv) > 1 else 'script.md'
    parsed = parse_script_file(md)
    
    # Print preview
    for sec in parsed:
        print('---')
        print('Section:', sec['section_header'])
        print(f'Frames: {sec["num_frames_detected"]}')
        for i, f in enumerate(sec['frames'], 1):
            preview = f[:120].replace('\n', ' ')
            print(f'  Frame {i}: {preview}{"..." if len(f) > 120 else ""}')