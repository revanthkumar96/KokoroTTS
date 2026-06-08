"""Download the two UK voice tensors into ./voices/."""
import os
import shutil
from huggingface_hub import hf_hub_download

VOICES = ["bf_emma", "bm_george"]


def main():
    os.makedirs("voices", exist_ok=True)
    for v in VOICES:
        src = hf_hub_download("hexgrad/Kokoro-82M", f"voices/{v}.pt")
        dst = f"voices/{v}.pt"
        shutil.copy(src, dst)
        print(f"OK {dst}")


if __name__ == "__main__":
    main()
