# Audio Summarizer

Turn any audio recording into a **plain-language summary** and a **full transcript**, saved together in one Markdown file.

- Works with WMA, M4A (Mac and Windows voice recorders), MP3, WAV, OGG, FLAC and more.
- Runs **on your own computer**. Free and open source. No accounts, no API keys, no paid services.
- English recordings, up to about 1 hour.

## What you get

Run:

```
uv run summarize "team meeting.wma"
```

It creates `team meeting_summary.md` next to the audio file:

```markdown
# Summary of team meeting.wma
- Date summarized: 2026-10-11
- Recording length: 42m 10s

## Summary
### Key points
- ...
### To-dos
- ...
### Decisions
- ...

## Full transcript
...
```

## How it works

1. **Reads the audio.** Any format is converted to one standard format. FFmpeg is built in, so there's nothing extra to install.
2. **Turns speech into text.** This uses [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (MIT license).
3. **Writes the summary.** This uses [IBM Granite 4.1 3B](https://huggingface.co/ibm-granite/granite-4.1-3b) (Apache 2.0 license), running locally. Long recordings are read in parts, then combined.

The first run downloads the models (about 0.5 GB for speech and 6 GB for the summary). After that, everything works offline.

## Setup (one time)

You need about **10 GB of free disk space** and **8 GB of RAM or more** (16 GB recommended).

### 1. Install Git and uv

**Mac** (open the Terminal app):

```bash
xcode-select --install
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows** (open PowerShell):

```powershell
winget install --id Git.Git -e
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Close the terminal and open a new one, then check that both work:

```
git --version
uv --version
```

You should see a version number for each.

### 2. Download this project

```
git clone https://github.com/kumr192/10_10_26_Claude_Code_Projects_001.git
cd 10_10_26_Claude_Code_Projects_001
uv sync
```

`uv sync` installs Python and all the libraries into a private `.venv` folder inside the project, so it doesn't touch the rest of your computer. This takes a few minutes.

## Use it

From inside the project folder:

```
uv run summarize "/path/to/recording.m4a"
```

On Windows, use a Windows path, for example `uv run summarize "C:\Users\me\Music\meeting.wma"`.

You'll see progress like this:

```
Step 1 of 2: turning speech into text for meeting.wma
  Loading speech model 'small.en' on cpu (first run downloads it)...
  Transcribing... 100%
  Done. Recording is 42m 10s long.
Step 2 of 2: writing the summary
  Loading summary model 'ibm-granite/granite-4.1-3b' on cpu (first run downloads ~6 GB)...
  Reading part 1 of 3...
  ...
Saved: /path/to/meeting_summary.md
```

### Options

| Option | What it does |
|---|---|
| `-o summary.md` | Save the result somewhere else |
| `--whisper-model base.en` | Faster but less accurate speech-to-text (`tiny.en`, `base.en`, `small.en` default, `medium.en`) |
| `--summary-model <name>` | Use a different Hugging Face model for the summary |

## How long does it take?

It depends on your computer. A machine with an NVIDIA graphics card or an Apple M-series chip is much faster. On a laptop with only a regular processor, a 1-hour recording can take **20 minutes or more**, and the summary step is the slow part. Use `--whisper-model base.en` to speed up the speech step.

## Troubleshooting

- **"Could not transcribe the audio"**: make sure the file plays in a normal media player. On the first run, check your internet connection.
- **Very slow or the computer freezes**: close other apps. The summary model needs about 7 GB of free memory.
- **`uv` or `git` not found**: close the terminal and open a new one after installing.

## License

Apache 2.0. See [LICENSE](LICENSE).
