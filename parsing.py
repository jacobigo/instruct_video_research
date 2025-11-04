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
    s = re.sub(r'(?m)^\s{0,3}#+\s.*$', '', s)          # headings
    s = re.sub(r'(?m)^\s*-{3,}\s*$', '', s)             # horizontal rules
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
    return s

# === Core parser ===

FRAME_MARKER_PAT = re.compile(
    r'(?P<marker>\*\*\(Click to Frame\s*\d+[^)]*\)\*\*|\*\*\[Frame[^\]]+\]\*\*|\[Frame[^\]]+\]|\*\*\(Begin[^\)]*\)\*\*)',
    flags=re.I
)

SECTION_HEADER = re.compile(r'(?m)^\s*##\s+Section\s+\d+[:\s].*$', flags=re.I)

FRAMES_COUNT_IN_SECTION = re.compile(r'\*\s*\((\d+)\s+frames\)\s*\*', flags=re.I)

def split_into_sections(text):
    """
    Return list of (section_header_text, section_body_text) tuples.
    If no leading sections, returns one section with header None.
    """
    sections = []
    # find indices of each section header
    idxs = [m.start() for m in SECTION_HEADER.finditer(text)]
    if not idxs:
        return [(None, text)]
    # get all matches with spans
    matches = list(SECTION_HEADER.finditer(text))
    for i, m in enumerate(matches):
        start = m.start()
        header = m.group(0)
        body_start = m.end()
        if i + 1 < len(matches):
            end = matches[i + 1].start()
        else:
            end = len(text)
        body = text[body_start:end].strip()
        sections.append((header.strip(), body))
    return sections

def extract_frames_from_section(header, body):
    """
    Given a section body, return an ordered list of frame texts (cleaned).
    Uses the explicit frame markers when available, else uses heuristics.
    """
    # Try to read declared frame count like "*(7 frames)*"
    count_match = FRAMES_COUNT_IN_SECTION.search(body)
    declared_count = int(count_match.group(1)) if count_match else None

    # Find all explicit frame marker matches and their spans
    markers = list(FRAME_MARKER_PAT.finditer(body))
    if markers:
        # If markers exist, split at their start positions; include trailing content until next marker or section end.
        chunks = []
        for i, m in enumerate(markers):
            start = m.start()
            if i + 1 < len(markers):
                end = markers[i + 1].start()
            else:
                end = len(body)
            chunk = body[start:end].strip()
            chunks.append(chunk)
        # If declared_count exists and differs from found markers, attempt to merge/split
        if declared_count and declared_count != len(chunks):
            # If we found fewer chunks than declared, try splitting chunks at '---' or blank-line boundaries
            if len(chunks) < declared_count:
                expanded = []
                for c in chunks:
                    parts = [p.strip() for p in re.split(r'\n-{3,}\n|\n{2,}', c) if p.strip()]
                    expanded.extend(parts)
                if len(expanded) >= declared_count:
                    chunks = expanded
                else:
                    # fallback: split by sentences into roughly declared_count pieces
                    text_for_split = '\n\n'.join(chunks)
                    chunks = smart_even_split(text_for_split, declared_count)
            # If more chunks than declared, merge last few
            elif len(chunks) > declared_count:
                # merge extra into last declared_count chunk
                keep = chunks[:declared_count-1]
                remainder = '\n\n'.join(chunks[declared_count-1:])
                keep.append(remainder)
                chunks = keep
        frames = [clean_text(strip_frame_marker(c)) for c in chunks]
        return frames

    # No explicit markers; try splitting by '---' separators
    chunks = [p.strip() for p in re.split(r'\n-{3,}\n', body) if p.strip()]
    if declared_count and len(chunks) == declared_count:
        return [clean_text(c) for c in chunks]

    # If declared_count given but chunks don't match, split paragraphs into declared_count
    paragraphs = [p.strip() for p in re.split(r'\n{2,}', body) if p.strip()]
    if declared_count:
        if len(paragraphs) >= declared_count:
            # merge paragraphs into declared_count groups evenly
            frames = paragraph_group_split(paragraphs, declared_count)
            return [clean_text(p) for p in frames]
        else:
            # fallback to sentence-based even split
            return [clean_text(p) for p in smart_even_split(body, declared_count)]

    # If no declared count, but we have paragraphs, treat each paragraph as a frame if it looks like frames
    if len(paragraphs) <= 12:  # arbitrary safety cap
        return [clean_text(p) for p in paragraphs]

    # Last resort: return the whole section cleaned as 1 frame
    return [clean_text(body)]

def strip_frame_marker(chunk):
    # Remove leading explicit frame markers like **(Click to Frame 2: ...)**
    chunk = re.sub(r'^\s*\*\*\(Click to Frame[^)]*\)\*\*', '', chunk, flags=re.I).strip()
    chunk = re.sub(r'^\s*\*\*\[Frame[^\]]+\]\*\*', '', chunk, flags=re.I).strip()
    chunk = re.sub(r'^\s*\[Frame[^\]]+\]', '', chunk, flags=re.I).strip()
    return chunk

def paragraph_group_split(paragraphs, groups):
    """Group paragraphs into `groups` buckets, preserving order, balancing lengths."""
    if groups <= 0:
        return ['\n\n'.join(paragraphs)]
    n = len(paragraphs)
    # naive distribution: roughly equal counts
    per = max(1, n // groups)
    out = []
    i = 0
    for g in range(groups-1):
        out.append('\n\n'.join(paragraphs[i:i+per]))
        i += per
    out.append('\n\n'.join(paragraphs[i:]))
    return out

def smart_even_split(text, n):
    """
    Split text into n chunks roughly even by sentence count.
    """
    import re
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
    if n <= 1 or len(sentences) <= n:
        # fallback: group some sentences so result length == n if possible
        if len(sentences) <= n:
            return [' '.join(sentences)]
        return [' '.join(sentences)]
    k = len(sentences) // n
    out = []
    i = 0
    for j in range(n-1):
        out.append(' '.join(sentences[i:i+k]))
        i += k
    out.append(' '.join(sentences[i:]))
    return out

# === Main entry ===

def parse_script_file(md_path, out_json='parsed_frames.json'):
    text = read_file(md_path)
    sections = split_into_sections(text)

    parsed = []
    for header, body in sections:
        frames = extract_frames_from_section(header, body)
        parsed.append({
            'section_header': header,
            'num_frames_detected': len(frames),
            'frames': frames
        })

    # Save JSON
    Path(out_json).write_text(json.dumps(parsed, indent=2, ensure_ascii=False), encoding='utf-8')
    return parsed

if __name__ == '__main__':
    import sys
    md = sys.argv[1] if len(sys.argv) > 1 else 'script.md'
    parsed = parse_script_file(md)
    print(f'Parsed {sum(len(s["frames"]) for s in parsed)} frames across {len(parsed)} sections')
    # optionally print a preview
    for sec in parsed:
        print('---')
        print('Section:', sec['section_header'])
        for i, f in enumerate(sec['frames'], 1):
            print(f'Frame {i} preview:', f[:120].replace('\n',' ') + ('...' if len(f)>120 else ''))

    text = []
    for section in parsed:
        text.extend(section['frames'])

    print(f"Parsed script from {md}")
    print(f"Total frames detected: {len(text)}")