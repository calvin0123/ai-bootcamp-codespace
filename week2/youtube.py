from pathlib import Path
from youtube_transcript_api import YouTubeTranscriptApi


def format_timestamp(seconds: float) -> str:
    """Convert seconds to H:MM:SS if > 1 hour, else M:SS"""
    total_seconds = int(seconds)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, secs = divmod(remainder, 60)

    if hours > 0:
        return f"{hours}:{minutes:02}:{secs:02}"
    else:
        return f"{minutes}:{secs:02}"


def make_subtitles(transcript) -> str:
    lines = []

    for entry in transcript:
        ts = format_timestamp(entry.start)
        text = entry.text.replace('\n', ' ')
        lines.append(ts + ' ' + text)

    return '\n'.join(lines)


def fetch_transcript_raw(video_id):
    ytt_api = YouTubeTranscriptApi()
    transcript = ytt_api.fetch(video_id)
    return transcript


def fetch_transcript_text(video_id):
    transcript = fetch_transcript_raw(video_id)
    subtitles = make_subtitles(transcript)
    return subtitles


def fetch_transcript_cached(video_id, cache_dir="../data_cache/youtube_videos"):
    cache_dir = Path(cache_dir)
    cache_file = cache_dir / f"{video_id}.txt"

    if cache_file.exists():
        return cache_file.read_text(encoding="utf-8")

    subtitles = fetch_transcript_text(video_id)
    cache_file.write_text(subtitles, encoding="utf-8")

    return subtitles


def fetch_youtube_transcript(video_id: str) -> str:
    """
    Fetches the transcript of a YouTube video and converts it into a subtitle-formatted string.

    

    Example:
    0:00 Hey everyone, welcome to our event. This
    0:02 event is brought to you by data talks
    0:03 club which is a community of people who
    0:05 love data. We have weekly events today.
    0:08 Uh this is one of such events. Um if you
    0:11 want to find out more about the events
    0:13 we have, there is a link in the
    0:14 description. Um so click on that link,
    0:16 check it out right now. We actually have
    0:19 quite a few events in our pipeline, but
    0:21 we need to put them on the website. Uh
    0:24 but keep a

    Args:
        video_id (str): The unique YouTube video ID.

    Returns:
        str: The subtitles generated from the video's transcript.
    """
    return fetch_transcript_text(video_id)