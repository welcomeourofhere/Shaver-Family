import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createHash } from "node:crypto";
const feedback = await import("../src/scripts/feedback.ts");
const config = JSON.parse(
  readFileSync(new URL("../src/config/feedback.json", import.meta.url)),
);

test("feedback preference survives reload and unavailable storage", () => {
  const values = new Map();
  const storage = {
    getItem: (key) => values.get(key) ?? null,
    setItem: (key, value) => values.set(key, value),
  };
  assert.equal(feedback.readFeedbackPreference(storage), true);
  feedback.saveFeedbackPreference(storage, false);
  assert.equal(feedback.readFeedbackPreference(storage), false);
  feedback.saveFeedbackPreference(storage, true);
  assert.equal(feedback.readFeedbackPreference(storage), true);
  const blocked = {
    getItem() {
      throw new Error("Blocked");
    },
    setItem() {
      throw new Error("Blocked");
    },
  };
  assert.equal(feedback.readFeedbackPreference(blocked), true);
  assert.doesNotThrow(() => feedback.saveFeedbackPreference(blocked, false));
});
test("rapid feedback is suppressed and disclosure tones follow the pre-activation state", () => {
  assert.equal(feedback.FEEDBACK_INTERVAL, 180);
  assert.equal(feedback.canPlayFeedback(0, -Infinity), true);
  assert.equal(feedback.canPlayFeedback(150, 100), false);
  assert.equal(feedback.canPlayFeedback(279, 100), false);
  assert.equal(feedback.canPlayFeedback(280, 100), true);
  assert.equal(feedback.canPlayFeedback(NaN, 100), false);
  assert.equal(feedback.canPlayFeedback(Infinity, 100), false);
  assert.equal(feedback.canPlayFeedback(50, 100), false);
  assert.equal(feedback.feedbackTone("disclosure", false), "open");
  assert.equal(feedback.feedbackTone("disclosure", true), "close");
  assert.equal(feedback.feedbackTone("selection"), "select");
  assert.equal(feedback.feedbackTone("media"), "select");
  for (const kind of ["filled", "text", "icon"])
    assert.equal(feedback.feedbackTone(kind), "tap");
});
test("one four-role registry owns local audio, volume, throttle and concise haptics", () => {
  assert.ok(config.volume > 0 && config.volume <= 0.5);
  assert.deepEqual(Object.keys(config.tones), ["tap", "select", "open", "close"]);
  assert.deepEqual(feedback.FEEDBACK_TONES, config.tones);
  const patterns = new Set();
  for (const [tone, settings] of Object.entries(config.tones)) {
    assert.equal(settings.url, `/audio/${tone}.wav`);
    const pattern = settings.hapticPattern;
    assert.ok(pattern.length > 0 && pattern.length <= 3 && pattern.length % 2 === 1);
    assert.ok(pattern.every((value) => Number.isInteger(value) && value > 0 && value <= 24));
    assert.ok(pattern.reduce((sum, value) => sum + value, 0) <= 50);
    patterns.add(JSON.stringify(pattern));
  }
  assert.equal(patterns.size, 4);
  const source = readFileSync(new URL("../src/scripts/feedback.ts", import.meta.url), "utf8");
  assert.doesNotMatch(source, /config\/design|--feedback-/);
});
test("only trusted touch or pen can vibrate, and reduced motion suppresses it", () => {
  for (const pointerType of ["touch", "pen"]) {
    assert.equal(feedback.canVibrateFeedback({ isTrusted: true, pointerType }, false), true);
    assert.equal(feedback.canVibrateFeedback({ isTrusted: false, pointerType }, false), false);
    assert.equal(feedback.canVibrateFeedback({ isTrusted: true, pointerType }, true), false);
  }
  for (const pointerType of ["mouse", "", undefined])
    assert.equal(feedback.canVibrateFeedback({ isTrusted: true, pointerType }, false), false);
});
test("four original short PCM WAVs are reproducible, unclipped and match provenance", () => {
  const manifest = JSON.parse(
    readFileSync(new URL("../content/feedback-sources.json", import.meta.url)),
  );
  assert.equal(manifest.origin, "original-procedural-synthesis");
  assert.equal(
    createHash("sha256").update(readFileSync(new URL(`../${manifest.generator}`, import.meta.url))).digest("hex"),
    manifest.generatorSha256,
  );
  assert.equal(manifest.clips.length, 4);
  assert.deepEqual(manifest.clips.map((clip) => clip.kind), Object.keys(config.tones));
  for (const clip of manifest.clips) {
    assert.equal(clip.url, config.tones[clip.kind].url);
    const bytes = readFileSync(
      new URL(`../public${clip.url}`, import.meta.url),
    );
    assert.equal(bytes.length, clip.bytes);
    assert.equal(createHash("sha256").update(bytes).digest("hex"), clip.sha256);
    assert.equal(bytes.toString("ascii", 0, 4), "RIFF");
    assert.equal(bytes.toString("ascii", 8, 12), "WAVE");
    assert.equal(bytes.readUInt32LE(4) + 8, bytes.length);
    const chunks = new Map();
    for (let offset = 12; offset + 8 <= bytes.length;) {
      const size = bytes.readUInt32LE(offset + 4);
      chunks.set(bytes.toString("ascii", offset, offset + 4), bytes.subarray(offset + 8, offset + 8 + size));
      offset += 8 + size + size % 2;
    }
    const format = chunks.get("fmt ");
    assert.equal(format.readUInt16LE(0), 1); // Uncompressed PCM.
    assert.equal(format.readUInt16LE(2), 1);
    assert.equal(format.readUInt32LE(4), 44100);
    assert.equal(format.readUInt16LE(14), 16);
    const data = chunks.get("data");
    assert.equal(data.length % 2, 0);
    const samples = Array.from({ length: data.length / 2 }, (_, index) => data.readInt16LE(index * 2));
    assert.equal(samples.length, clip.samples);
    const duration = samples.length / 44100 * 1000;
    assert.equal(Number(duration.toFixed(6)), clip.durationMs);
    assert.ok(duration > 0 && duration <= 220);
    if (clip.kind === "tap") assert.ok(duration >= 50 && duration <= 70);
    if (clip.kind === "select") assert.ok(duration >= 100 && duration <= 140);
    const peak = Math.max(...samples.map(Math.abs)) / 32768;
    assert.equal(Number(peak.toFixed(6)), clip.peak);
    assert.ok(peak > 0.1 && peak < 0.5);
    assert.ok(samples.every((sample) => sample > -32768 && sample < 32767));
    assert.equal(samples[0], 0);
    assert.ok(Math.abs(samples.at(-1)) <= 2);
  }
});
