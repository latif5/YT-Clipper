"""
Viral segment analyzer.
Detects the most engaging parts of a video based on subtitle analysis.
"""

import re
from typing import List, Dict
from .utils import print_step, print_success, print_clips_summary


# Keywords that often indicate viral/engaging content (Indonesian + English)
VIRAL_KEYWORDS = [
    # Indonesian excitement
    "gila", "parah", "wah", "wow", "anjir", "astagfirullah", "astaga",
    "serius", "beneran", "masa", "kok bisa", "gimana", "mantap", "hebat",
    "keren", "luar biasa", "dahsyat", "gokil", "sumpah", "demi apa",
    # Financial/content specific
    "rugi", "untung", "profit", "loss", "naik", "turun", "meledak",
    "jatuh", "crash", "boom", "rally", "bangkrut", "kaya", "miskin",
    # English equivalents  
    "crazy", "insane", "amazing", "incredible", "unbelievable", "wow",
    "shocking", "huge", "massive", "explode", "crash", "boom",
    # Emotional markers
    "hahaha", "wkwk", "lol", "ketawa", "nangis", "sedih", "senang",
]

# Question words often indicate interesting discussion
QUESTION_WORDS = [
    "kenapa", "mengapa", "gimana", "bagaimana", "apa", "apakah",
    "kapan", "siapa", "dimana", "berapa", "why", "how", "what",
]


def analyze_viral_segments(
    subtitles: List[Dict],
    num_clips: int = 3,
    min_duration: float = 60.0,
    max_duration: float = 180.0,
    target_duration: float = 120.0,
) -> List[Dict]:
    """
    Analyze subtitles to find the most viral/engaging segments.
    
    Args:
        subtitles: List of subtitle entries with start, end, text
        num_clips: Number of clips to return
        min_duration: Minimum clip duration in seconds
        max_duration: Maximum clip duration in seconds
        target_duration: Target clip duration
        
    Returns:
        List of clip definitions with start, end, score
    """
    print_step("Analyzing", "Searching for viral segments...")
    
    if not subtitles:
        print_success("No subtitles, using default segments")
        # Return evenly spaced clips
        total_duration = 3000  # Default 50 min
        segment_length = target_duration
        return [
            {"start": i * (total_duration / num_clips), 
             "end": i * (total_duration / num_clips) + segment_length,
             "score": 0}
            for i in range(num_clips)
        ]
    
    # Calculate scores for sliding windows
    total_duration = subtitles[-1]["end"]
    window_scores = []
    
    # Use sliding window with step
    step = 10  # 10 second steps
    
    for start in range(0, int(total_duration - min_duration), step):
        for duration in [min_duration, target_duration, max_duration]:
            end = start + duration
            if end > total_duration:
                continue
            
            score = calculate_segment_score(subtitles, start, end)
            window_scores.append({
                "start": float(start),
                "end": float(end),
                "score": score,
                "duration": duration,
            })
    
    # Sort by score
    window_scores.sort(key=lambda x: x["score"], reverse=True)
    
    # Select top non-overlapping segments
    selected = []
    for segment in window_scores:
        # Check for overlap with already selected
        overlaps = False
        for sel in selected:
            if segments_overlap(segment, sel):
                overlaps = True
                break
        
        if not overlaps:
            selected.append(segment)
            if len(selected) >= num_clips:
                break
    
    # Sort by start time
    selected.sort(key=lambda x: x["start"])
    
    print_success(f"Found {len(selected)} viral segments")
    print_clips_summary(selected)
    
    return selected


def calculate_segment_score(subtitles: List[Dict], start: float, end: float) -> float:
    """Calculate viral score for a segment."""
    score = 0.0
    word_count = 0
    
    for sub in subtitles:
        # Check if subtitle overlaps with segment
        if sub["end"] < start or sub["start"] > end:
            continue
        
        text = sub["text"].lower()
        words = text.split()
        word_count += len(words)
        
        # Keyword scoring
        for keyword in VIRAL_KEYWORDS:
            if keyword in text:
                score += 10
        
        # Question scoring (indicates discussion)
        for qword in QUESTION_WORDS:
            if qword in text:
                score += 5
        
        # Exclamation marks indicate excitement
        score += text.count("!") * 3
        
        # Laughing indicators
        if "haha" in text or "wkwk" in text or "lol" in text:
            score += 8
        
        # Numbers often indicate interesting data
        if re.search(r"\d+%|\d+\s*(juta|miliar|ribu|k|m|b)", text):
            score += 7
    
    # Word density bonus (more words = more engagement)
    duration = end - start
    if duration > 0:
        density = word_count / duration
        score += density * 5
    
    return score


def segments_overlap(seg1: Dict, seg2: Dict, min_gap: float = 30.0) -> bool:
    """Check if two segments overlap (with minimum gap requirement)."""
    return not (seg1["end"] + min_gap < seg2["start"] or seg2["end"] + min_gap < seg1["start"])


def adjust_segment_boundaries(
    segment: Dict,
    subtitles: List[Dict],
) -> Dict:
    """
    Adjust segment boundaries to start/end at natural breaks.
    """
    start = segment["start"]
    end = segment["end"]
    
    # Find subtitle that starts closest to segment start
    for sub in subtitles:
        if abs(sub["start"] - start) < 5:
            start = sub["start"]
            break
    
    # Find subtitle that ends closest to segment end
    for sub in reversed(subtitles):
        if abs(sub["end"] - end) < 5:
            end = sub["end"]
            break
    
    return {**segment, "start": start, "end": end}
