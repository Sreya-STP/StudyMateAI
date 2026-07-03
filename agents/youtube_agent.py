# agents/youtube_agent.py

import re
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
)


def _extract_video_id(url: str) -> str:
    """
    Extract the YouTube video ID from any common URL format.
    """
    patterns = [
        r"(?:v=)([a-zA-Z0-9_-]{11})",       # ?v=ID
        r"youtu\.be/([a-zA-Z0-9_-]{11})",    # youtu.be/ID
        r"embed/([a-zA-Z0-9_-]{11})",         # embed/ID
        r"shorts/([a-zA-Z0-9_-]{11})",        # shorts/ID
        r"live/([a-zA-Z0-9_-]{11})",          # live/ID  
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    raise ValueError(
        "Could not extract a YouTube video ID from the URL. "
        "Please paste a standard YouTube link e.g. https://www.youtube.com/watch?v=..."
    )


def get_youtube_transcript(url: str) -> str:
    """
    Fetch the transcript for a YouTube video and return it as clean plain text.

    Tries English first. If English isn't found, grabs whatever language IS 
    available and attempts to auto-translate it to English using YouTube's API.
    If translation fails, passes the foreign text directly so the LLM can translate it.
    """
    if not url or not url.strip():
        raise ValueError("No YouTube URL provided.")

    video_id = _extract_video_id(url.strip())

    try:
        # V1.2+ SYNTAX: We MUST instantiate the object!
        ytt_api = YouTubeTranscriptApi()
        
        # Use the new .list() method to get all available transcripts
        transcript_data = ytt_api.list(video_id)
        
        try:
            # 1. Try to find an English transcript first
            transcript = transcript_data.find_transcript(["en", "en-US", "en-GB", "en-IN"])
        except NoTranscriptFound:
            # 2. Safely grab the first available transcript using an iterator
            transcript = next(iter(transcript_data), None)
            
            if transcript is None:
                raise ValueError(
                    "No subtitles or transcripts could be found for this video in any language."
                )
            
            # 3. Tell YouTube's API to auto-translate it to English if possible
            if transcript.is_translatable:
                try:
                    transcript = transcript.translate('en')
                except Exception:
                    pass # If translation fails, pass the foreign text to Gemini!

        # Fetch the actual text blocks
        transcript_list = transcript.fetch()

        # V1.2+ SYNTAX: The API returns objects now, so we MUST use seg.text
        segments = [seg.text.strip() for seg in transcript_list if seg.text.strip()]
        
        paragraphs = []
        chunk_size = 10
        for i in range(0, len(segments), chunk_size):
            paragraphs.append(" ".join(segments[i : i + chunk_size]))

        text = "\n\n".join(paragraphs)

        if not text.strip():
            raise ValueError("Transcript was fetched but appears to be empty.")

        return text

    except TranscriptsDisabled:
        raise ValueError(
            "Transcripts are disabled for this video. "
            "The video owner has turned off captions — try a different video."
        )
    except VideoUnavailable:
        raise ValueError(
            "This video is unavailable (private, deleted, or region-locked)."
        )
    except NoTranscriptFound:
        raise ValueError(
            "No subtitles or transcripts could be found for this video in any language."
        )
    except ValueError:
        raise   
    except Exception as e:
        raise ValueError(f"Could not fetch transcript: {str(e)}")