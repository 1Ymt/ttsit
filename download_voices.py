from huggingface_hub import snapshot_download

REPO_ID = "hexgrad/Kokoro-82M"
LOCAL_DIR = "voices"

if __name__ == "__main__":
    path = snapshot_download(
        repo_id=REPO_ID,
        allow_patterns=["voices/*.pt", "config.json", "kokoro-v1_0.pth"],
        local_dir=LOCAL_DIR,
    )
    print(f"Voices downloaded into: {path}")
