"""Step 2: summarize the transcript in plain language with IBM Granite."""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

DEFAULT_MODEL = "ibm-granite/granite-4.1-3b"
CHUNK_WORDS = 2500  # about 15-20 minutes of talking

STYLE = (
    "Write in very simple, everyday English. Use short sentences. "
    "Avoid jargon. If the speakers use a technical term or acronym, explain it in a few plain words. "
    "Only use facts from the transcript. Do not make anything up."
)

NOTES_PROMPT = (
    "Below is part of a recording transcript. Write short bullet-point notes covering "
    "what was said, any tasks people agreed to do, and any decisions made.\n"
    f"{STYLE}\n\nTranscript:\n{{text}}"
)

FINAL_PROMPT = (
    "Below is {source}. Turn it into a summary using exactly this Markdown layout:\n\n"
    "### Key points\n- (5 to 10 bullets on what was said)\n\n"
    "### To-dos\n- (tasks someone needs to do, with who and when if mentioned)\n\n"
    "### Decisions\n- (things that were agreed or decided)\n\n"
    "If there are no to-dos or no decisions, write '- None mentioned.' under that heading.\n"
    f"{STYLE}\n\n{{text}}"
)


def pick_device() -> tuple[str, torch.dtype]:
    """NVIDIA GPU, then Apple Silicon GPU, then plain CPU."""
    if torch.cuda.is_available():
        return "cuda", torch.bfloat16
    if torch.backends.mps.is_available():
        return "mps", torch.float16
    return "cpu", torch.bfloat16


class Summarizer:
    def __init__(self, model_name: str = DEFAULT_MODEL):
        self.device, dtype = pick_device()
        print(f"  Loading summary model '{model_name}' on {self.device} (first run downloads ~6 GB)...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name, dtype=dtype)
        self.model.to(self.device)
        self.model.eval()

    def ask(self, prompt: str, max_new_tokens: int = 700) -> str:
        messages = [{"role": "user", "content": prompt}]
        inputs = self.tokenizer.apply_chat_template(
            messages, add_generation_prompt=True, return_tensors="pt", return_dict=True
        ).to(self.device)
        with torch.no_grad():
            output = self.model.generate(**inputs, max_new_tokens=max_new_tokens, do_sample=False)
        new_tokens = output[0][inputs["input_ids"].shape[1]:]
        return self.tokenizer.decode(new_tokens, skip_special_tokens=True).strip()


def split_into_chunks(text: str, chunk_words: int = CHUNK_WORDS) -> list[str]:
    words = text.split()
    return [" ".join(words[i:i + chunk_words]) for i in range(0, len(words), chunk_words)]


def summarize(transcript: str, model_name: str = DEFAULT_MODEL) -> str:
    if not transcript.strip():
        return "_No speech was found in this recording._"

    summarizer = Summarizer(model_name)
    chunks = split_into_chunks(transcript)

    if len(chunks) == 1:
        print("  Writing summary...")
        return summarizer.ask(FINAL_PROMPT.format(source="a recording transcript", text=transcript))

    # Long recording: take notes on each part first, then summarize the notes.
    notes = []
    for number, chunk in enumerate(chunks, start=1):
        print(f"  Reading part {number} of {len(chunks)}...")
        notes.append(summarizer.ask(NOTES_PROMPT.format(text=chunk), max_new_tokens=500))

    print("  Writing final summary...")
    all_notes = "\n\n".join(f"Notes for part {i}:\n{n}" for i, n in enumerate(notes, start=1))
    return summarizer.ask(FINAL_PROMPT.format(source="a set of notes from one recording, in order", text=all_notes))
