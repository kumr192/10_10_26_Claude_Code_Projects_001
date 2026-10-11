"""Step 1: read any audio file and turn speech into text with faster-whisper."""

from pathlib import Path

from faster_whisper import WhisperModel
from faster_whisper.audio import decode_audio

SAMPLE_RATE = 16000  # Whisper expects 16 kHz mono audio


def load_audio(path: Path):
    """Decode any audio format (WMA, M4A, MP3, WAV, ...) into 16 kHz mono samples.

    faster-whisper uses PyAV, which ships its own copy of FFmpeg,
    so users do not need to install FFmpeg separately.
    """
    return decode_audio(str(path), sampling_rate=SAMPLE_RATE)


def pick_whisper_device() -> tuple[str, str]:
    """Use an NVIDIA GPU when there is one, otherwise the CPU."""
    import ctranslate2

    if ctranslate2.get_cuda_device_count() > 0:
        return "cuda", "float16"
    # int8 keeps memory low and is the fastest option on a normal laptop CPU
    return "cpu", "int8"


def run_whisper(audio, duration: float, model_name: str, device: str, compute_type: str) -> list[str]:
    print(f"  Loading speech model '{model_name}' on {device} (first run downloads it)...")
    model = WhisperModel(model_name, device=device, compute_type=compute_type)

    # vad_filter skips long silences, which makes it faster and avoids made-up text
    segments, _info = model.transcribe(audio, language="en", vad_filter=True)

    lines = []
    for segment in segments:
        done = min(segment.end / duration, 1.0) if duration else 1.0
        print(f"\r  Transcribing... {done:4.0%}", end="", flush=True)
        lines.append(segment.text.strip())
    print()
    return lines


def transcribe(path: Path, model_name: str = "small.en") -> tuple[str, float]:
    """Return (transcript text, audio length in seconds)."""
    audio = load_audio(path)
    duration = len(audio) / SAMPLE_RATE

    device, compute_type = pick_whisper_device()
    try:
        lines = run_whisper(audio, duration, model_name, device, compute_type)
    except Exception as error:
        if device == "cpu":
            raise
        # An NVIDIA card is present but its CUDA libraries (e.g. cublas64_12.dll) are missing.
        print(f"\n  GPU not usable ({error}). Switching to CPU, which is slower but works everywhere.")
        lines = run_whisper(audio, duration, model_name, "cpu", "int8")
    return "\n".join(lines), duration
