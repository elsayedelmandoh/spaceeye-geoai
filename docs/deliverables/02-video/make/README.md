Video rebuild kit (02-video/)
- cards.js -> out/title.png, end.png and the transparent speaker caption insert_caption.png (from text/*.txt)
- logos.js -> out/logos.png
- assemble.py [out_dir] [timing_file] -> out_dir/intro.mp4 (reads the timing file, stills/, out/*, narration); timing_file defaults to timing.json
- Two versions, identical pictures: timing.json = human voice (gamal-ramzy-cloned-voice.wav) -> ../intro-human-voice.mp4; timing-ai.json = AI voice (ai-voice-narration.wav) -> ../intro-ai-voice.mp4
- Optional "inserts" in a timing file: interview clips (../khaled-abbas-1..3.mp4) spliced after the title card with their own sound, the speaker caption and the logos; everything after them shifts together, so narration sync is kept.
- Run order: node cards.js out; node logos.js out; python assemble.py out; copy out/intro.mp4 to ../intro-human-voice.mp4; then python assemble.py out timing-ai.json and copy out/intro.mp4 to ../intro-ai-voice.mp4
- Env: NODE_PATH=/.../node_modules; FFMPEG=/.../ffmpeg-static/ffmpeg
