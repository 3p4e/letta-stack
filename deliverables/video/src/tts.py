#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate Macedonian narration via ElevenLabs eleven_v3, measure durations,
and emit a timeline.json the renderers use to stay in sync."""
import json, os, re, subprocess, sys, time, urllib.request, urllib.error
import imageio_ffmpeg
from narration import FILM1, FILM1_VOICE, FILM2, FILM2_VOICE

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
KEY = os.environ["ELEVENLABS_API_KEY"]
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio")
os.makedirs(OUT, exist_ok=True)

TAIL_PAD = 0.65   # seconds of silence after each segment, for breathing room
HEAD_PAD = 0.40   # lead-in before the first word of a scene


def synth(voice_id, seg, prev_text, next_text, path, retries=3):
    if os.path.exists(path) and os.path.getsize(path) > 8000:
        return "cached"
    # eleven_v3 rejects previous_text/next_text; stability must be 0.0 / 0.5 / 1.0
    body = json.dumps({
        "text": seg["text"],
        "model_id": "eleven_v3",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.8},
    }).encode()
    url = (f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
           f"?output_format=mp3_44100_128")
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, data=body, headers={
                "xi-api-key": KEY, "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=180) as r:
                data = r.read()
            if len(data) < 4000:
                raise RuntimeError(f"suspiciously small payload: {len(data)}B")
            with open(path, "wb") as f:
                f.write(data)
            return "ok"
        except Exception as e:
            last = e
            detail = ""
            if isinstance(e, urllib.error.HTTPError):
                detail = e.read()[:300].decode("utf-8", "replace")
            print(f"    retry {attempt+1}/{retries} after {e} {detail}", flush=True)
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"TTS failed for {seg['id']}: {last}")


def duration(path):
    p = subprocess.run([FFMPEG, "-hide_banner", "-i", path],
                       capture_output=True, text=True)
    m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", p.stderr)
    if not m:
        raise RuntimeError(f"no duration for {path}\n{p.stderr[-500:]}")
    h, mi, s = m.groups()
    return int(h) * 3600 + int(mi) * 60 + float(s)


def build(film_key, segs, voice):
    print(f"\n=== {film_key} ===")
    scenes, t = [], 0.0
    for i, seg in enumerate(segs):
        path = os.path.join(OUT, f"{film_key}_{seg['id']}.mp3")
        prev_t = segs[i - 1]["text"] if i > 0 else ""
        next_t = segs[i + 1]["text"] if i + 1 < len(segs) else ""
        status = synth(voice, seg, prev_t, next_t, path)
        d = duration(path)
        start = t + HEAD_PAD
        total = HEAD_PAD + d + TAIL_PAD
        scenes.append(dict(id=seg["id"], scene=seg["scene"], file=os.path.basename(path),
                           text=seg["text"], audio_start=round(start, 3),
                           audio_dur=round(d, 3), scene_start=round(t, 3),
                           scene_dur=round(total, 3)))
        t += total
        print(f"  {seg['id']} {seg['scene']:<10} {status:<7} audio {d:6.2f}s  "
              f"scene {t - total:7.2f} → {t:7.2f}")
    print(f"  TOTAL RUNTIME: {t:.2f}s ({int(t//60)}:{t % 60:04.1f})")
    return dict(film=film_key, voice=voice, fps=24, w=1920, h=1080,
                total=round(t, 3), head_pad=HEAD_PAD, tail_pad=TAIL_PAD, scenes=scenes)


def master_audio(tl, out_path):
    """Concatenate segment mp3s with the head/tail silence padding baked in."""
    inputs, filt = [], []
    for i, sc in enumerate(tl["scenes"]):
        inputs += ["-i", os.path.join(OUT, sc["file"])]
        filt.append(f"[{i}:a]aresample=44100,"
                    f"adelay={int(tl['head_pad']*1000)}|{int(tl['head_pad']*1000)},"
                    f"apad=pad_dur={tl['tail_pad']}[a{i}]")
    chain = ";".join(filt) + ";" + "".join(f"[a{i}]" for i in range(len(tl["scenes"])))
    chain += f"concat=n={len(tl['scenes'])}:v=0:a=1[out]"
    cmd = [FFMPEG, "-y", "-hide_banner", "-loglevel", "error", *inputs,
           "-filter_complex", chain, "-map", "[out]",
           "-c:a", "aac", "-b:a", "192k", out_path]
    subprocess.run(cmd, check=True)
    print(f"  master audio → {out_path} ({duration(out_path):.2f}s)")


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "both"
    jobs = []
    if which in ("both", "film1"):
        jobs.append(("film1", FILM1, FILM1_VOICE))
    if which in ("both", "film2"):
        jobs.append(("film2", FILM2, FILM2_VOICE))
    for key, segs, voice in jobs:
        tl = build(key, segs, voice)
        with open(f"{key}_timeline.json", "w") as f:
            json.dump(tl, f, ensure_ascii=False, indent=1)
        master_audio(tl, os.path.join(OUT, f"{key}_master.m4a"))
    print("\ndone.")
