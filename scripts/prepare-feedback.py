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
    "tap": (112, 0.22, "Dry muted mechanical switch: 60ms audible body and 52ms silent decoder tail"),
    "select": (112, 0.22, "Two short bright muted toggles, G4–C5"),
    "open": (152, 0.23, "Soft rising reed sweep, B3–F-sharp4"),
    "close": (128, 0.22, "Short falling wooden latch, A3–D3"),
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
                    body = (math.sin(math.tau * 164.813778 * local) * 0.52 +
                            math.sin(math.tau * 494.441334 * local) * 0.10)
                    value += strength * (body + filtered_noise * 0.18) * math.exp(-local * 125)
        elif kind == "select":
            for start, frequency, strength in [(0.0, 391.995436, 1.0), (0.044, 523.251131, 0.78)]:
                local = time - start
                if 0 <= local < 0.068:
                    value += strength * (math.sin(math.tau * frequency * local) +
                              math.sin(math.tau * frequency * 2 * local) * 0.035) * math.exp(-local * 58) * window(local, 0.068, 0.001, 0.012)
        elif kind == "open":
            phase = math.tau * (246.941651 * time + (369.994423 - 246.941651) * time * time / (2 * duration_ms / 1000))
            reed = math.sin(phase) + math.sin(phase * 3) * 0.11 + math.sin(phase * 5) * 0.025
            value = (reed + filtered_noise * 0.025) * math.exp(-time * 9) * window(time, duration_ms / 1000, 0.002, 0.028)
        else:
            phase = math.tau * (220 * time + (146.832384 - 220) * time * time / (2 * duration_ms / 1000))
            latch = math.sin(phase) * 0.7 + math.sin(phase * 2) * 0.16
            value = (latch + filtered_noise * 0.11 * math.exp(-time * 100)) * math.exp(-time * 40) * window(time, duration_ms / 1000, 0.001, 0.018)
        # Smooth both edges, including the click, to avoid codec/device pops.
        value *= window(time, 0.060 if kind == "tap" else duration_ms / 1000, 0.0015, 0.006)
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
        "revisedOn": "2026-11-17",
        "direction": "Four quiet distinct functional cues: mechanical action, higher two-step selection, rising reed opening and short wooden closing. Fast smoothed attacks; no copied melodies.",
        "originalManifest": "content/feedback-originals/2026-11-05.json",
        "originalGenerator": "content/feedback-originals/prepare-feedback-2026-11-05.py.txt",
        "format": {"encoding": "PCM signed 16-bit little-endian", "channels": 1, "sampleRateHz": SAMPLE_RATE},
        "clips": [],
    }
    outputs = {}
    for kind, (duration_ms, peak, description) in SPECS.items():
        data, pcm = render(kind, duration_ms, peak)
        pcm_peak = max(map(abs, pcm))
        url = f"/audio/67/{kind}.wav"
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
            "audibleWindowMs": 60 if kind == "tap" else duration_ms,
            "peak": round(pcm_peak / 32768, 6),
            "rms": round(math.sqrt(sum(value * value for value in pcm) / len(pcm)) / 32768, 6),
            "onset10PercentPeakMs": round(next(index for index, value in enumerate(pcm) if abs(value) >= pcm_peak * 0.1) / SAMPLE_RATE * 1000, 6),
            "peakAtMs": round(max(range(len(pcm)), key=lambda index: abs(pcm[index])) / SAMPLE_RATE * 1000, 6),
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
