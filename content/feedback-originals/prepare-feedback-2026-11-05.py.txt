"""Generate the original SOYUZ feedback family; no recordings or dependencies.

Run: python scripts/prepare-feedback.py
Check reproducibility without writing: python scripts/prepare-feedback.py --check
"""

import argparse
import hashlib
import io
import json
import math
from pathlib import Path
import random
import struct
import wave


ROOT = Path(__file__).resolve().parents[1]
SAMPLE_RATE = 44100
SPECS = {
    "tap": (60, 0.22, "Muted warm radio-button click"),
    "select": (128, 0.24, "Two soft low radio notes, G3–C4"),
    "open": (208, 0.24, "Warm muted-organ ascending phrase, G3–C4–E4"),
    "close": (208, 0.24, "Warm muted-organ descending phrase, E4–C4–G3"),
}


def window(time, duration, attack=0.010, release=0.024):
    if time <= 0 or time >= duration:
        return 0.0
    return min(1.0, time / attack) * min(1.0, (duration - time) / release)


def render(kind, duration_ms, peak):
    samples = []
    noise = random.Random(1949 + list(SPECS).index(kind))
    previous_noise = 0.0
    for index in range(round(SAMPLE_RATE * duration_ms / 1000)):
        time = index / SAMPLE_RATE
        random_sample = noise.uniform(-1, 1)
        # A single filtered noise family gives each cue a small radio/mechanical edge.
        filtered_noise = previous_noise * 0.7 + random_sample * 0.3
        previous_noise = filtered_noise
        value = 0.0
        if kind == "tap":
            for start, strength in [(0.0, 1.0), (0.019, 0.32)]:
                local = time - start
                if 0 <= local < 0.041:
                    body = (math.sin(math.tau * 196 * local) * 0.52 +
                            math.sin(math.tau * 392 * local) * 0.06)
                    value += strength * (body + filtered_noise * 0.14) * math.exp(-local * 125)
        elif kind == "select":
            for start, frequency in [(0.0, 195.997718), (0.057, 261.625565)]:
                local = time - start
                if 0 <= local < 0.071:
                    value += (math.sin(math.tau * frequency * local) +
                              math.sin(math.tau * frequency * 2 * local) * 0.07 +
                              filtered_noise * 0.02) * math.exp(-local * 40) * window(local, 0.071)
        else:
            notes = [195.997718, 261.625565, 329.627557]
            if kind == "close":
                notes.reverse()
            for note, frequency in enumerate(notes):
                local = time - note * 0.064
                if 0 <= local < 0.080:
                    brass = sum(math.sin(math.tau * frequency * harmonic * local) * strength
                                for harmonic, strength in [(1, 1.0), (2, 0.10), (3, 0.025)])
                    value += (math.tanh(brass * 0.9) + filtered_noise * 0.015) * window(local, 0.080)
        # Smooth both edges, including the click, to avoid codec/device pops.
        value *= window(time, duration_ms / 1000, 0.0015, 0.006)
        samples.append(value)
    scale = peak * 32767 / max(abs(value) for value in samples)
    pcm = [round(value * scale) for value in samples]
    output = io.BytesIO()
    with wave.open(output, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes(struct.pack(f"<{len(pcm)}h", *pcm))
    return output.getvalue(), pcm


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Compare generated output without writing")
    args = parser.parse_args()
    manifest = {
        "origin": "original-procedural-synthesis",
        "createdOn": "2026-11-05",
        "generator": "scripts/prepare-feedback.py",
        "generatorSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "method": "Deterministic additive/noise synthesis using Python standard library; no third-party recordings, melodies, voices or network sources.",
        "direction": "Quiet warm radio/organ family: lower register, softened attacks and reduced harmonics; original retro cues without copied melodies.",
        "format": {"encoding": "PCM signed 16-bit little-endian", "channels": 1, "sampleRateHz": SAMPLE_RATE},
        "clips": [],
    }
    outputs = {}
    for kind, (duration_ms, peak, description) in SPECS.items():
        data, pcm = render(kind, duration_ms, peak)
        url = f"/audio/{kind}.wav"
        outputs[ROOT / "public" / url.lstrip("/")] = data
        manifest["clips"].append({
            "kind": kind,
            "url": url,
            "description": description,
            "operation": "original-procedural-synthesis",
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "samples": len(pcm),
            "durationMs": round(len(pcm) / SAMPLE_RATE * 1000, 6),
            "peak": round(max(abs(value) for value in pcm) / 32768, 6),
            "rms": round(math.sqrt(sum(value * value for value in pcm) / len(pcm)) / 32768, 6),
        })
    outputs[ROOT / "content" / "feedback-sources.json"] = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    for path, data in outputs.items():
        if args.check:
            if not path.exists() or path.read_bytes() != data:
                raise SystemExit(f"OUT OF DATE: {path.relative_to(ROOT)}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    print(f"{'Verified' if args.check else 'Generated'} 4 original WAVs and provenance manifest")


if __name__ == "__main__":
    main()
