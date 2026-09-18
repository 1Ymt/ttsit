import sys, os, threading
import argparse
import uvicorn
import base64
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from kokoro import KModel, KPipeline
import numpy as np

REPO_ID = "hexgrad/Kokoro-82M"
SAMPLE_RATE = 24_000

VOICES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "voices")
MODEL_CONFIG = os.path.join(VOICES_DIR, "config.json")
MODEL_WEIGHTS = os.path.join(VOICES_DIR, "kokoro-v1_0.pth")

#Language code mapping used for Kokoro model. Convert BCP-47 tags to Kokoro's internal language codes 
LANG_MAP = {
    "en": "a", "en-us": "a", "en-gb": "b",
    "es": "e", "fr": "f", "hi": "h", "it": "i",
    "ja": "j", "pt": "p", "pt-br": "p", "zh": "z",
}

app = FastAPI()
_pipelines :dict[str, KPipeline] = {}


class SynthesizeRequest(BaseModel):
    text: str   # one sentence, already whitespace-normalised by the Java side
    voice: str = "af_heart"
    speed: float = 1.0  # 0.5 .. 2.0
    lang: str = "a" # BCP-47 tag

class SynthesizeResponse(BaseModel):
    sample_rate: int
    pcm16_base64: str   # mono, 16-bit little-endian PCM, base64

#Caching pipelines for each Language code
def createPipeline(lang_tag: str) -> KPipeline:
    code = LANG_MAP.get(lang_tag.lower())
    if code is None:
        raise HTTPException(400, f"unsupported language: {lang_tag}")
    if code not in _pipelines:
        _pipelines[code] = KPipeline(lang_code=code, repo_id=REPO_ID, model=KModel(repo_id=REPO_ID, config=MODEL_CONFIG, model=MODEL_WEIGHTS))
    return _pipelines[code]

def getVoicePath(voice: str) -> str:
    return os.path.join(VOICES_DIR, "voices", f"{voice}.pt")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/synthesize")
def synthesize(req: SynthesizeRequest):
    voice_path = getVoicePath(req.voice)
    pipeline = createPipeline(req.lang)

    # Step 1. Run the pipeline to generate audio samples
    chunks = [] #Incase the sentence is too long and was automatically split into multiple chunks
    for result in pipeline(text=req.text, voice=voice_path, speed=req.speed):
        samples = result.audio.cpu().numpy()
        chunks.append(samples)

    # Put chunks together into a single array. If there were no chunks, return an empty array.
    audio = np.concatenate(chunks) if chunks else np.zeros(0, dtype=np.float32)

    # Clip array, in case the model overshoots 1.0 slightly
    audio = np.clip(audio, -1.0, 1.0)

    # Step 2. Scale to 16-bit integer range and convert. Lay the integers out as raw bytes
    pcm16 = (audio * 32767).astype("<i2").tobytes()   # "<i2" = little-endian, 2-byte signed int

    # Step 3. Convert bytes to base64 string for transport
    b64_str = base64.b64encode(pcm16).decode()

    return SynthesizeResponse(sample_rate=SAMPLE_RATE, pcm16_base64=b64_str)

#Fallback when the parent process dies, so that the server doesn't keep running in the background
def watch_parent():
    sys.stdin.read()
    os._exit(0)  


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=0)  
    ap.add_argument("--lang", default="en")  
    args = ap.parse_args()

    port = args.port
    createPipeline(args.lang)   #Pre-caching the pipeline for fist request
    
    threading.Thread(target=watch_parent, daemon=True).start()
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")
