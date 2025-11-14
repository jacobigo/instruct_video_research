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

    # Replace remaining asterisks
    s = s.replace('*', '')

    return s

# === Core parser ===

# Strong frame boundary markers - these DEFINITELY indicate a new frame
STRONG_FRAME_MARKER = re.compile(
    r'(?:^\s*\*\*\s*\[(?:Click to )?Frame\s*\d+\]\s*\*\*\s*$|'
    r'^\s*\*\*\s*\[Advance to Frame\s*\d+\]\s*\*\*\s*$)',
    flags=re.I | re.M
)

# Pattern to match "Frame X Continued" markers (to be removed)
FRAME_CONTINUED_PAT = re.compile(
    r'^\s*\*\*\s*\[Frame\s*\d+\s+Continued\]\s*\*\*\s*$',
    flags=re.I | re.M
)

# Transition phrases that are NOT frame boundaries (just conversational flow)
FALSE_TRANSITIONS = re.compile(
    r'(?i)(?:let\'?s|now let\'?s|let me|moving on|next|finally|first|second|consider|'
    r'think about|imagine|as we|before we|with that|having said)',
    flags=re.I
)

SECTION_HEADER = re.compile(r'(?m)^\s*##\s+Section\s+\d+[:\s].*$', flags=re.I)
FRAMES_COUNT_IN_SECTION = re.compile(r'\*\s*\((\d+)\s+frames\)\s*\*', flags=re.I)

def split_into_sections(text):
    """
    Return list of (section_header_text, section_body_text) tuples.
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
    """Remove 'Frame X Continued' markers."""
    return FRAME_CONTINUED_PAT.sub('', text)

def is_strong_frame_boundary(line):
    """Check if a line is a strong frame boundary marker."""
    return bool(STRONG_FRAME_MARKER.match(line.strip()))

def extract_frames_from_section(header, body):
    """
    Extract frames using only STRONG frame markers, ignoring conversational transitions.
    """
    # Remove "Frame X Continued" markers
    body = remove_frame_continued_markers(body)
    
    # Get declared count
    count_match = FRAMES_COUNT_IN_SECTION.search(body)
    declared_count = int(count_match.group(1)) if count_match else None
    
    # Split by lines to find strong markers
    lines = body.split('\n')
    
    # Find indices of strong frame markers
    marker_indices = []
    for i, line in enumerate(lines):
        if is_strong_frame_boundary(line):
            marker_indices.append(i)
    
    # If we have strong markers, use them
    if marker_indices:
        frames = []
        
        # Add initial content before first marker if substantial
        if marker_indices[0] > 0:
            initial = '\n'.join(lines[:marker_indices[0]]).strip()
            if len(initial) > 100:  # Only if substantial content
                frames.append(initial)
        
        # Extract content between markers
        for i, marker_idx in enumerate(marker_indices):
            # Start after the marker line
            start = marker_idx + 1
            
            # End at next marker or end of section
            if i + 1 < len(marker_indices):
                end = marker_indices[i + 1]
            else:
                end = len(lines)
            
            chunk = '\n'.join(lines[start:end]).strip()
            if chunk:  # Only add non-empty chunks
                frames.append(chunk)
        
        # Clean frames
        cleaned_frames = [clean_text(f) for f in frames if len(f.strip()) > 50]
        
        # Check against declared count
        if declared_count:
            if len(cleaned_frames) == declared_count:
                return cleaned_frames
            elif len(cleaned_frames) < declared_count:
                # Try to split large frames
                return split_to_target_count(cleaned_frames, declared_count)
            else:
                # More frames than expected - try to merge smaller ones
                return merge_to_target_count(cleaned_frames, declared_count)
        
        return cleaned_frames
    
    # No strong markers found - fall back to heuristic splitting
    return fallback_split(body, declared_count)

def split_to_target_count(frames, target):
    """Split frames to reach target count by dividing large frames."""
    if len(frames) >= target:
        return frames[:target]
    
    # Find the largest frame(s) and split them
    while len(frames) < target:
        # Find longest frame
        longest_idx = max(range(len(frames)), key=lambda i: len(frames[i]))
        longest = frames[longest_idx]
        
        # Split by double newlines
        parts = [p.strip() for p in longest.split('\n\n') if p.strip()]
        
        if len(parts) <= 1:
            break  # Can't split further
        
        # Split into two roughly equal parts
        mid = len(parts) // 2
        part1 = '\n\n'.join(parts[:mid])
        part2 = '\n\n'.join(parts[mid:])
        
        # Replace the longest frame with its parts
        frames = frames[:longest_idx] + [part1, part2] + frames[longest_idx+1:]
    
    return frames[:target]

def merge_to_target_count(frames, target):
    """Merge frames to reach target count by combining smaller frames."""
    if len(frames) <= target:
        return frames
    
    # Merge smallest adjacent frames until we reach target
    while len(frames) > target:
        # Find smallest frame
        smallest_idx = min(range(len(frames)), key=lambda i: len(frames[i]))
        
        # Merge with next frame (or previous if it's the last)
        if smallest_idx < len(frames) - 1:
            frames[smallest_idx] = frames[smallest_idx] + '\n\n' + frames[smallest_idx + 1]
            frames.pop(smallest_idx + 1)
        else:
            frames[smallest_idx - 1] = frames[smallest_idx - 1] + '\n\n' + frames[smallest_idx]
            frames.pop(smallest_idx)
    
    return frames

def fallback_split(body, declared_count):
    """Fallback method when no strong markers found."""
    # Try triple-dashes
    hr_pattern = re.compile(r'\n\s*-{3,}\s*\n')
    chunks = [c.strip() for c in hr_pattern.split(body) if c.strip()]
    
    if declared_count and len(chunks) == declared_count:
        return [clean_text(c) for c in chunks]
    
    # Split by substantial paragraph breaks
    paragraphs = [p.strip() for p in re.split(r'\n\n+', body) if len(p.strip()) > 100]
    
    if not declared_count:
        return [clean_text(p) for p in paragraphs]
    
    # Group paragraphs to match declared count
    if len(paragraphs) <= declared_count:
        return [clean_text(p) for p in paragraphs]
    
    return group_paragraphs_evenly(paragraphs, declared_count)

def group_paragraphs_evenly(paragraphs, target_count):
    """Group paragraphs into target_count frames."""
    if target_count <= 0:
        return ['\n\n'.join(paragraphs)]
    
    if len(paragraphs) <= target_count:
        return [clean_text(p) for p in paragraphs]
    
    per_frame = len(paragraphs) // target_count
    remainder = len(paragraphs) % target_count
    
    frames = []
    idx = 0
    
    for i in range(target_count):
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
    warnings = []
    
    for header, body in sections:
        frames = extract_frames_from_section(header, body)
        
        #post processing empty frames
        frames = [frame if frame.strip() else "_" for frame in frames]
        
        total_frames += len(frames)
        
        # Check for discrepancies
        count_match = FRAMES_COUNT_IN_SECTION.search(body)
        declared = int(count_match.group(1)) if count_match else None
        
        if declared and len(frames) != declared:
            warnings.append(f"Section '{header}' declares {declared} frames but extracted {len(frames)}")
        
        parsed.append({
            'section_header': header,
            'declared_frames': declared,
            'num_frames_detected': len(frames),
            'frames': frames
        })

    # Save JSON
    Path(out_json).write_text(json.dumps(parsed, indent=2, ensure_ascii=False), encoding='utf-8')
    
    print(f'\nParsing Summary:')
    print(f'Total sections: {len(parsed)}')
    print(f'Total frames extracted: {total_frames}')
    
    if warnings:
        print(f'\nWarnings ({len(warnings)}):')
        for w in warnings:
            print(f'  - {w}')
    else:
        print('\n✓ All sections match declared frame counts!')
    
    return parsed

if __name__ == '__main__':
    import sys
    md = sys.argv[1] if len(sys.argv) > 1 else 'content_ch1s/topics_in_rl/script.md'
    parsed = parse_script_file(md)
    
    # Print preview
    print('\n' + '='*60)
    print('FRAME PREVIEW:')
    print('='*60)
    for sec in parsed:
        print(f"\n{sec['section_header']}")
        print(f"Declared: {sec['declared_frames']}, Extracted: {sec['num_frames_detected']}")
        for i, f in enumerate(sec['frames'], 1):
            preview = f[:100].replace('\n', ' ')
            print(f"  Frame {i}: {preview}{'...' if len(f) > 100 else ''}")