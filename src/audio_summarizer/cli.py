"""Command line entry point: `uv run summarize "my meeting.wma"`."""

import argparse
import sys
import time
from datetime import date
from pathlib import Path

from .summarize import DEFAULT_MODEL, summarize
from .transcribe import transcribe


def format_duration(seconds: float) -> str:
    minutes, secs = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes}m {secs}s" if hours else f"{minutes}m {secs}s"


def build_markdown(audio: Path, duration: float, summary: str, transcript: str) -> str:
    return (
        f"# Summary of {audio.name}\n\n"
        f"- **Date summarized:** {date.today().isoformat()}\n"
        f"- **Recording length:** {format_duration(duration)}\n\n"
        f"## Summary\n\n{summary}\n\n"
        f"## Full transcript\n\n{transcript}\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="summarize",
        description="Turn an audio recording into a plain-language summary plus transcript (one Markdown file).",
    )
    parser.add_argument("audio", type=Path, help="Path to the audio file (WMA, M4A, MP3, WAV, ...)")
    parser.add_argument("-o", "--output", type=Path, help="Where to save the Markdown file (default: next to the audio)")
    parser.add_argument(
        "--whisper-model",
        default="small.en",
        help="Speech model size: tiny.en, base.en, small.en (default), medium.en. Bigger = more accurate but slower.",
    )
    parser.add_argument("--summary-model", default=DEFAULT_MODEL, help="Hugging Face model used for the summary")
    args = parser.parse_args()

    audio: Path = args.audio.expanduser()
    if not audio.is_file():
        sys.exit(f"Could not find the file: {audio}")
    output = args.output or audio.with_name(f"{audio.stem}_summary.md")

    start = time.time()
    print(f"Step 1 of 2: turning speech into text for {audio.name}")
    try:
        transcript, duration = transcribe(audio, args.whisper_model)
    except Exception as error:
        sys.exit(
            f"Could not transcribe the audio: {error}\n"
            "Check that the file plays in a media player. On the first run, also check your "
            "internet connection, because the speech model is downloaded once."
        )
    print(f"  Done. Recording is {format_duration(duration)} long.")

    print("Step 2 of 2: writing the summary")
    try:
        summary = summarize(transcript, args.summary_model)
    except Exception as error:
        sys.exit(
            f"Could not write the summary: {error}\n"
            "On the first run, check your internet connection, because the summary model "
            "(about 6 GB) is downloaded once. Also check you have enough free memory (8 GB+)."
        )

    output.write_text(build_markdown(audio, duration, summary, transcript), encoding="utf-8")
    print(f"\n{summary}\n")
    print(f"Saved: {output}  (took {format_duration(time.time() - start)})")


if __name__ == "__main__":
    main()
