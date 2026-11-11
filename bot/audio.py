"""Voices (free Microsoft Hindi neural voices), sound effects and audio mixing."""
import asyncio
import os
import re
import subprocess
import time
import wave

import numpy as np

SR = 44100

# Each character gets its own voice by shifting pitch/speed of the 2 Hindi voices.
VOICES = {
    "narrator": ("hi-IN-MadhurNeural", "+0%", "+0Hz"),
    "chintu": ("hi-IN-SwaraNeural", "+12%", "+45Hz"),
    "pinky": ("hi-IN-SwaraNeural", "+10%", "+70Hz"),
    "mummy": ("hi-IN-SwaraNeural", "+4%", "+0Hz"),
    "papa": ("hi-IN-MadhurNeural", "+2%", "-4Hz"),
    "dadi": ("hi-IN-SwaraNeural", "-8%", "-22Hz"),
    "guptaji": ("hi-IN-MadhurNeural", "-4%", "-18Hz"),
}


# ---------------------------------------------------------------- text to speech
async def _edge(text, voice, rate, pitch, out_mp3):
    import edge_tts
    comm = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    got = False
    with open(out_mp3, "wb") as f:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
                got = True
    if not got:
        raise RuntimeError("No audio was received")


def _speak_once(text, who, out_mp3):
    voice, rate, pitch = VOICES.get(who, VOICES["narrator"])
    err = None
    for wait in (0, 3, 10, 25, 45):
        time.sleep(wait)
        try:
            asyncio.run(_edge(text, voice, rate, pitch, out_mp3))
            return
        except Exception as e:  # free service sometimes throttles
            err = e
    raise RuntimeError(f"Text-to-speech failed for {who}: {err}")


def speak(text, who, out_wav, offline=False):
    """Make one spoken line as a mono WAV. Returns the samples (int16)."""
    if offline:  # silent placeholder with a speech-like envelope, for testing without internet
        n = int(SR * (0.35 + 0.075 * len(text.split()) * 1.6))
        t = np.arange(n) / SR
        a = (np.sin(2 * np.pi * 180 * t) * (0.5 + 0.5 * np.sin(2 * np.pi * 4 * t)) * 3000).astype(np.int16)
        _write(out_wav, a)
        return a
    mp3 = out_wav + ".mp3"
    try:
        _speak_once(text, who, mp3)
    except RuntimeError:
        parts = [p for p in re.split(r"(?<=[।!?.])\s+", text.strip()) if p]
        if len(parts) < 2:
            raise
        chunks = []
        for i, p in enumerate(parts):
            _speak_once(p, who, f"{mp3}.{i}.mp3")
            chunks.append(_decode(f"{mp3}.{i}.mp3"))
        _write(out_wav, np.concatenate(chunks))
        return _read(out_wav)
    a = _decode(mp3)
    _write(out_wav, a)
    return a


def _decode(path):
    tmp = path + ".wav"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", path, "-ar", str(SR), "-ac", "1", tmp], check=True)
    return _read(tmp)


def _read(path):
    with wave.open(path) as w:
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)


def _write(path, a):
    with wave.open(path, "wb") as w:
        w.setnchannels(1), w.setsampwidth(2), w.setframerate(SR)
        w.writeframes(np.asarray(a, dtype=np.int16).tobytes())


def envelope(a, fps):
    """Loudness per video frame (0..1), used for lip-sync."""
    hop = SR / fps
    n = int(np.ceil(len(a) / hop))
    x = a.astype(np.float32) / 32768
    env = np.array([np.sqrt(np.mean(x[int(i * hop):int((i + 1) * hop)] ** 2) + 1e-9) for i in range(n)])
    return env / (np.percentile(env, 95) + 1e-6)


# ---------------------------------------------------------------- sound effects (generated, no files needed)
def sfx(name):
    t = lambda d: np.arange(int(SR * d)) / SR  # noqa: E731
    if name == "boing":
        tt = t(0.45)
        f = 180 + 260 * np.exp(-tt * 6) * np.sin(2 * np.pi * 9 * tt) + 120
        y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 5)
    elif name == "whoosh":
        tt = t(0.5)
        noise = np.random.default_rng(1).normal(0, 1, len(tt))
        k = np.convolve(noise, np.ones(40) / 40, mode="same")
        y = k * np.sin(np.pi * tt / tt[-1]) * 2.2
    elif name == "pop":
        tt = t(0.12)
        y = np.sin(2 * np.pi * (900 - 4000 * tt) * tt) * np.exp(-tt * 40)
    elif name == "ding":
        tt = t(0.9)
        y = (np.sin(2 * np.pi * 1320 * tt) + 0.5 * np.sin(2 * np.pi * 1980 * tt)) * np.exp(-tt * 5) * 0.6
    elif name == "punchline":  # ba-dum-tss
        parts = []
        for f0, d in ((140, 0.13), (110, 0.13)):
            tt = t(d)
            parts.append(np.sin(2 * np.pi * f0 * tt) * np.exp(-tt * 25))
        tt = t(0.5)
        n = np.random.default_rng(2).normal(0, 1, len(tt))
        hp = n - np.convolve(n, np.ones(6) / 6, mode="same")
        parts.append(hp * np.exp(-tt * 7) * 0.6)
        y = np.concatenate(parts)
    elif name == "gasp":
        tt = t(0.35)
        n = np.random.default_rng(3).normal(0, 1, len(tt))
        y = np.convolve(n, np.ones(12) / 12, mode="same") * np.sin(np.pi * tt / tt[-1]) * 1.5
    else:
        return np.zeros(1, dtype=np.int16)
    return (np.clip(y, -1, 1) * 9000).astype(np.int16)


def mix(total_sec, voice_clips, sfx_clips, music_path=None, music_vol=0.08):
    """voice_clips / sfx_clips: [(start_sec, int16 array)]. Returns float32 mix."""
    out = np.zeros(int(SR * (total_sec + 0.5)), dtype=np.float32)
    for st, a in voice_clips + sfx_clips:
        i = int(st * SR)
        seg = a.astype(np.float32)[: max(0, len(out) - i)]
        out[i:i + len(seg)] += seg
    if music_path and os.path.exists(music_path):
        mtmp = music_path + ".mix.wav"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-stream_loop", "-1", "-i", music_path, "-t",
                        f"{total_sec + 0.5:.2f}", "-ar", str(SR), "-ac", "1", mtmp], check=True)
        m = _read(mtmp).astype(np.float32)[: len(out)]
        out[: len(m)] += m * music_vol
    peak = np.abs(out).max() or 1
    if peak > 30000:
        out *= 30000 / peak
    return out.astype(np.int16)


def save(path, a):
    _write(path, a)
