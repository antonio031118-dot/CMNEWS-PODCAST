#!/usr/bin/env python3
"""Generate the CMNEWS podcast audio from a plain-text script.

Usage:
    ELEVENLABS_API_KEY=... python3 generate_podcast_audio.py script.txt output.mp3

The script text file uses blank lines to separate paragraphs. "CMNEWS" should
already be written as "Si, Em, News" wherever it should be spoken (this
controls pronunciation; the visible brand name everywhere else stays CMNEWS).

Process: split into small sentence-level chunks (long single TTS calls lose
volume partway through), generate each chunk, flag/regenerate any chunk whose
raw loudness is a big outlier, normalize every chunk individually to -16 LUFS,
then concatenate with short silences between chunks.
"""
import json
import os
import re
import subprocess
import sys
import tempfile

VOICE_ID = "6VhI0BBMzbLqzPaeqUCz"  # "Victor" - Spanish (Spain) male voice
MODEL_ID = "eleven_multilingual_v2"
VOICE_SETTINGS = {"stability": 0.5, "similarity_boost": 0.85, "style": 0.35, "use_speaker_boost": True}
LOUDNESS_OUTLIER_LUFS = -28.0
TARGET_LUFS = "-16"


def api_key():
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        sys.exit("Set ELEVENLABS_API_KEY in the environment before running this script.")
    return key


def split_sentences(paragraph):
    parts = re.split(r"(?<=[.!?])\s+", paragraph)
    return [s.strip() for s in parts if s.strip()]


def chunk_script(text, max_chars=260, max_sentences=2):
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    for p in paragraphs:
        cur, cur_len = [], 0
        for s in split_sentences(p):
            if cur and (cur_len + len(s) > max_chars or len(cur) >= max_sentences):
                chunks.append(" ".join(cur))
                cur, cur_len = [], 0
            cur.append(s)
            cur_len += len(s)
        if cur:
            chunks.append(" ".join(cur))
    return chunks


def tts_chunk(text, out_path, key):
    payload = json.dumps({"text": text, "model_id": MODEL_ID, "voice_settings": VOICE_SETTINGS})
    subprocess.run(
        ["curl", "-sS", "-o", out_path,
         "-H", f"xi-api-key: {key}",
         "-H", "Content-Type: application/json",
         "-X", "POST", f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}",
         "-d", payload],
        check=True,
    )


def measure_lufs(path):
    out = subprocess.run(
        ["ffmpeg", "-i", path, "-af", "loudnorm=print_format=summary", "-f", "null", "-"],
        capture_output=True, text=True,
    ).stderr
    m = re.search(r"Input Integrated:\s*(-?\d+\.\d+)", out)
    return float(m.group(1)) if m else None


def normalize(in_path, out_path):
    subprocess.run(
        ["ffmpeg", "-y", "-i", in_path, "-af",
         f"loudnorm=I={TARGET_LUFS}:TP=-1.5:LRA=11", "-ar", "44100",
         "-codec:a", "libmp3lame", "-b:a", "128k", out_path],
        check=True, capture_output=True,
    )


def make_silence(path, seconds=0.35):
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=mono",
         "-t", str(seconds), "-q:a", "4", path],
        check=True, capture_output=True,
    )


def main():
    if len(sys.argv) != 3:
        sys.exit("Usage: generate_podcast_audio.py <script.txt> <output.mp3>")
    script_path, output_path = sys.argv[1], sys.argv[2]
    key = api_key()
    text = open(script_path, encoding="utf-8").read()
    chunks = chunk_script(text)
    print(f"{len(chunks)} chunks")

    with tempfile.TemporaryDirectory() as tmp:
        silence = os.path.join(tmp, "silence.mp3")
        make_silence(silence)

        norm_paths = []
        for i, chunk_text in enumerate(chunks):
            raw = os.path.join(tmp, f"raw_{i:02d}.mp3")
            tts_chunk(chunk_text, raw, key)
            lufs = measure_lufs(raw)
            print(f"chunk {i:02d}: {lufs} LUFS")
            if lufs is not None and lufs < LOUDNESS_OUTLIER_LUFS:
                print(f"  -> outlier, regenerating (up to 2 retries)")
                for _ in range(2):
                    tts_chunk(chunk_text, raw, key)
                    lufs = measure_lufs(raw)
                    print(f"  retry: {lufs} LUFS")
                    if lufs is not None and lufs >= LOUDNESS_OUTLIER_LUFS:
                        break
            norm = os.path.join(tmp, f"norm_{i:02d}.mp3")
            normalize(raw, norm)
            norm_paths.append(norm)

        concat_list = os.path.join(tmp, "concat.txt")
        with open(concat_list, "w") as f:
            for p in norm_paths:
                f.write(f"file '{p}'\n")
                f.write(f"file '{silence}'\n")

        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list,
             "-acodec", "libmp3lame", "-b:a", "128k", output_path],
            check=True, capture_output=True,
        )
    print(f"done: {output_path}")


if __name__ == "__main__":
    main()
