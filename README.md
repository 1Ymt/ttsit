# ttsit

A small FastAPI text-to-speech server built on [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M).
It exposes one HTTP endpoint that turns a sentence into PCM audio, and is meant
to be run as a local subprocess (see [ttsit-client](https://github.com/1Ymt/ttsit-client),
the JavaFX GUI that drives it), though it works standalone with any HTTP client.

## Usage

Once the server is running (see below), synthesize a sentence with a plain HTTP call:

```
curl -X POST http://127.0.0.1:<port>/synthesize \
  -H "Content-Type: application/json" \
  -d "{\"text\": \"Hello there.\", \"voice\": \"af_heart\", \"speed\": 1.0, \"lang\": \"en\"}"
```

This returns a JSON body with the sample rate and base64-encoded PCM audio
(see the [API](#api) section below). In practice this server is started and
called by [ttsit-client](https://github.com/1Ymt/ttsit-client), which handles
splitting text into sentences and playing the audio back.

## Setup

```
python -m venv venv
venv\Scripts\activate        # or source venv/bin/activate on Linux/macOS
pip install -r requirements.txt
python download_voices.py    # fetches config.json, kokoro-v1_0.pth and voice files into voices/
```

## Running

```
python ttsserver.py --port <port>
```

The server listens on `127.0.0.1:<port>`.

## API

### `GET /health`
Returns `{"status": "ok"}` once the server is up.

### `POST /synthesize`
Synthesizes one sentence.

Request body:

```json
{
  "text": "Hello there.",
  "voice": "af_heart",
  "speed": 1.0,
  "lang": "en"
}
```

| field | type   | notes                                             |
|-------|--------|----------------------------------------------------|
| text  | string | one sentence to synthesize                         |
| voice | string | voice id, matching a `.pt` file in `voices/voices/` |
| speed | float  | playback speed multiplier (0.5 – 2.0)               |
| lang  | string | BCP-47 tag, e.g. `en`, `en-gb`, `es`, `ja`          |

Response body:

```json
{
  "sample_rate": 24000,
  "pcm16_base64": "..."
}
```

`pcm16_base64` is mono, 16-bit little-endian PCM, base64-encoded.

## License

MIT — see [LICENSE](LICENSE). The [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M)
model weights and voicepacks this server downloads at setup time are licensed
separately by their authors under Apache 2.0.
