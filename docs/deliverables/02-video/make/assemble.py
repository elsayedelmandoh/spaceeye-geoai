"""Assemble intro.mp4 from the stills, the rendered cards, the logo overlay and the narration.

Shot lengths come from the timing file (default timing.json; timing-ai.json for the AI voice; each shot spans one spoken part of the narration).
Run cards.js and logos.js first, then:
    FFMPEG=/path/to/ffmpeg python assemble.py [out_dir] [timing_file]
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
    timing_file = Path(sys.argv[2]) if len(sys.argv) > 2 else HERE / "timing.json"
    timing = json.loads(timing_file.read_text(encoding="utf-8"))
    plan = [(out_dir / "title.png", timing["title_seconds"], "in", None)]
    plan += [(out_dir / f"{s['card']}.png" if "card" in s else HERE / "stills" / s["still"],
              s["seconds"], s["zoom"], s.get("crop")) for s in timing["shots"]]
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
    spliced = timing.get("inserts") or timing.get("cards_before_end")
    base = out_dir / ("base.mp4" if spliced else "intro.mp4")
    run([*inputs, "-filter_complex", ";".join(graph), "-map", "[v]", "-map", "[a]",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-c:a", "aac", "-b:a", "160k",
         "-t", f"{total}", "-movflags", "+faststart", str(base)])
    current = base
    if timing.get("cards_before_end"):  # silent cards between the last shot and the end card
        cards = [card_part(out_dir, c["card"], c["seconds"], i) for i, c in enumerate(timing["cards_before_end"])]
        current = splice(current, bounds[-2] - half, cards, out_dir / "stage_cards.mp4")
    if timing.get("inserts"):  # interview clips right after the title card
        clips_in = [insert_part(HERE / clip, out_dir, i) for i, clip in enumerate(timing["inserts"])]
        current = splice(current, timing["title_seconds"] - half, clips_in, out_dir / "stage_inserts.mp4")
    if spliced:
        current.replace(out_dir / "intro.mp4")
    print(out_dir / "intro.mp4")


def duration(path: Path) -> float:
    """Length in seconds, read from ffmpeg's input summary (ffprobe is not always shipped)."""
    # ffmpeg exits non-zero when given no output file; the summary on stderr is all we need.
    info = subprocess.run([FFMPEG, "-hide_banner", "-i", str(path)], capture_output=True, text=True, check=False).stderr
    h, m, s = info.split("Duration: ")[1].split(",")[0].split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def insert_part(clip: Path, out_dir: Path, index: int) -> Path:
    """One interview clip with its own sound, short fades, the speaker caption and the logos."""
    length = duration(clip)
    part = out_dir / f"insert_{index:02d}.mp4"
    graph = (f"[0:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,"
             f"fps={FPS},format=yuv420p[b];[b][1:v]overlay=0:0[c];[c][2:v]overlay=0:0,"
             f"fade=t=in:st=0:d=0.3,fade=t=out:st={length - 0.3:.3f}:d=0.3[v];"
             f"[0:a]aformat=channel_layouts=stereo:sample_rates=48000,loudnorm=I=-18:TP=-2,"
             f"afade=t=in:st=0:d=0.15,afade=t=out:st={length - 0.25:.3f}:d=0.25[a]")
    run(["-i", str(clip), "-i", str(out_dir / "insert_caption.png"), "-i", str(out_dir / "logos.png"),
         "-filter_complex", graph, "-map", "[v]", "-map", "[a]", "-t", f"{length:.3f}",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-c:a", "aac", "-b:a", "160k", str(part)])
    return part


def card_part(out_dir: Path, card: str, seconds: float, index: int) -> Path:
    """A rendered card (out_dir/<card>.png) with the logos and silent audio, faded in and out."""
    part = out_dir / f"card_{index:02d}.mp4"
    graph = (f"[0:v]scale=1920:1080,fps={FPS},format=yuv420p[b];[b][1:v]overlay=0:0,"
             f"fade=t=in:st=0:d=0.4,fade=t=out:st={seconds - 0.4:.3f}:d=0.4[v]")
    run(["-loop", "1", "-t", f"{seconds:.3f}", "-i", str(out_dir / f"{card}.png"), "-i", str(out_dir / "logos.png"),
         "-f", "lavfi", "-t", f"{seconds:.3f}", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
         "-filter_complex", graph, "-map", "[v]", "-map", "2:a", "-t", f"{seconds:.3f}",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-c:a", "aac", "-b:a", "160k", str(part)])
    return part


def splice(base: Path, cut: float, parts: list[Path], out: Path) -> Path:
    """Insert parts into base at `cut` seconds; picture and narration after the cut shift together."""
    pieces = [(base, 0.0, cut), *[(p, None, None) for p in parts], (base, cut, None)]
    inputs = []
    for src, start, end in pieces:
        if start is not None:
            inputs += ["-ss", f"{start:.3f}"]
        if end is not None:
            inputs += ["-t", f"{end - start:.3f}"]
        inputs += ["-i", str(src)]
    n = len(pieces)
    graph = (";".join(f"[{i}:a]aformat=channel_layouts=stereo:sample_rates=48000[a{i}]" for i in range(n))
             + ";" + "".join(f"[{i}:v][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[v][a]")
    run([*inputs, "-filter_complex", graph, "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset",
         "veryfast", "-crf", "22", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(out)])
    shift = sum(duration(p) for p in parts)
    print(f"spliced {len(parts)} part(s), {shift:.2f} s, at {cut:.2f} s; later times move by that much")
    return out


if __name__ == "__main__":
    main()
