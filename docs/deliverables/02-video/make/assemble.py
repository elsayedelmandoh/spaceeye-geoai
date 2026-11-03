"""Assemble intro.mp4 from the stills, the rendered cards, the logo overlay and the narration.

Shot lengths come from timing.json (each shot spans one spoken part of the narration).
Run cards.js and logos.js first, then:
    FFMPEG=/path/to/ffmpeg python assemble.py [out_dir]
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FFMPEG = os.environ.get("FFMPEG", "ffmpeg")
FPS = 30
FADE = 0.4
XFADE = 0.5  # crossfade length; each cut is centred on its timing.json boundary
ZOOM_RANGE = 0.15
SIZE = "1920x1080"


def run(args: list[str]) -> None:
    subprocess.run([FFMPEG, "-hide_banner", "-loglevel", "error", "-y", *args], check=True)


def shot_clip(image: Path, seconds: float, zoom: str, crop: str | None, out: Path, fades: str = "") -> None:
    """One still as a clip with a slow zoom; `fades` adds extra fade filters (e.g. fade from black)."""
    frames = round(seconds * FPS)
    rate = ZOOM_RANGE / frames
    z = f"1+{rate}*on" if zoom == "in" else f"{1 + ZOOM_RANGE}-{rate}*on"
    pre = f"crop={crop}," if crop else ""
    vf = (f"{pre}scale=3840:2160,zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
          f":d={frames}:s={SIZE}:fps={FPS}{fades},format=yuv420p")
    run(["-loop", "1", "-i", str(image), "-vf", vf, "-frames:v", str(frames),
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", str(out)])


def main() -> None:
    out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    timing = json.loads((HERE / "timing.json").read_text(encoding="utf-8"))
    plan = [(out_dir / "title.png", timing["title_seconds"], "in", None)]
    plan += [(HERE / "stills" / s["still"], s["seconds"], s["zoom"], s.get("crop")) for s in timing["shots"]]
    plan.append((out_dir / "end.png", timing["end_seconds"], "in", None))

    # Clip i spans [B(i-1)-X/2, B(i)+X/2] so the crossfade at boundary B(i) is centred on it;
    # first/last clips only extend on their inner side. Total length stays sum(seconds).
    half = XFADE / 2
    bounds, acc = [], 0.0
    for p in plan:
        acc += p[1]
        bounds.append(acc)
    clips = []
    for i, (image, seconds, zoom, crop) in enumerate(plan):
        length = seconds + (XFADE if 0 < i < len(plan) - 1 else half)
        fades = ",fade=t=in:st=0:d=0.8" if i == 0 else ""  # title text fades up from black
        clip = out_dir / f"clip_{i:02d}.mp4"
        shot_clip(image, length, zoom, crop, clip, fades)
        clips.append(clip)

    total = sum(p[1] for p in plan)
    delay_ms = int(timing["title_seconds"] * 1000)
    narration = (HERE / timing["narration"]).resolve()
    logos = out_dir / "logos.png"
    n = len(clips)
    inputs = [x for c in clips for x in ("-i", str(c))] + ["-i", str(narration)]
    graph, prev = [], "[0:v]"
    for i in range(n - 1):
        kind = "fadeblack" if i == n - 2 else "fade"  # end card rises out of black
        label = f"[x{i}]"
        graph.append(f"{prev}[{i + 1}:v]xfade=transition={kind}:duration={XFADE}:offset={bounds[i] - half:.3f}{label}")
        prev = label
    if logos.exists():
        inputs += ["-i", str(logos)]
        graph.append(f"{prev}[{n + 1}:v]overlay=0:0,fade=t=out:st={total - 0.8:.3f}:d=0.8[v]")
    else:
        graph.append(f"{prev}fade=t=out:st={total - 0.8:.3f}:d=0.8[v]")
    print("cuts (s):", [round(b, 2) for b in bounds[:-1]])
    graph.append(f"[{n}:a]aformat=channel_layouts=stereo,adelay={delay_ms}|{delay_ms},apad,"
                 f"afade=t=out:st={total - 1}:d=1[a]")
    run([*inputs, "-filter_complex", ";".join(graph), "-map", "[v]", "-map", "[a]",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-c:a", "aac", "-b:a", "160k",
         "-t", f"{total}", "-movflags", "+faststart", str(out_dir / "intro.mp4")])
    print(out_dir / "intro.mp4")


if __name__ == "__main__":
    main()
