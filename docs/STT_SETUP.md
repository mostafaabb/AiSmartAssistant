  # Speech-to-Text (STT) Setup

This document explains how to configure the STT endpoint added to NexusAI and test it locally.

Supported providers

- `local` - runs a local `whisper` CLI if installed on the host.
- `assemblyai` - uploads audio and transcribes via AssemblyAI API (requires API key).
- `openai` - uses OpenAI's audio transcription endpoint (requires API key).

Configuration

1. Copy `.env.example` to `.env` and set values.

- Choose provider:

```
STT_PROVIDER=assemblyai   # or openai or local
```

- If using AssemblyAI:

```
ASSEMBLYAI_API_KEY=your_assemblyai_key_here
```

- If using OpenAI:

```
OPENAI_API_KEY=sk-...
```

- Optional: set `REDIS_URL` if you plan to enable workers or collaborative presence.

Running locally (development)

1. Activate your Python venv and install requirements:

```bash
python -m venv venv
venv\Scripts\activate    # Windows
pip install -r ai_smart_assistant/requirements.txt
```

2. Start the Flask app (ensure `.env` is loaded or env vars exported):

```bash
python run.py
```

3. From the browser, open the app and use the voice button. If your browser does not support Web Speech API, the client will record audio and POST it to `/stt` for transcription.

Test with curl

You can test the `/stt` endpoint directly with a file:

```bash
curl -X POST -F "audio=@path/to/recording.webm" http://127.0.0.1:5000/stt
```

Troubleshooting

- If `STT_PROVIDER=local` and you see `Local whisper CLI not installed`, install `whisper` or switch to a hosted provider.

- For AssemblyAI/OpenAI errors, check that keys are set and the host has network access.

- If transcription times out, increase polling timeout in `ai_smart_assistant/app/routes.py` or check provider status.

Security

- Never commit your `.env` file.
- Do not expose API keys in client-side code.

Next steps

- Add background workers for long-running transcriptions and improve UX with progress indicators.
- Add server-side rate limiting and quotas for STT usage.
