Video rebuild kit (02-video/)
- cards.js -> out/title.png, end.png (from text/*.txt)
- logos.js -> out/logos.png
- assemble.py -> out/intro.mp4 (reads timing.json, stills/, out/*, narration)
- Run order: node cards.js out; node logos.js out; python assemble.py out; copy out/intro.mp4 to ../intro.mp4
- Env: NODE_PATH=/.../node_modules; FFMPEG=/.../ffmpeg-static/ffmpeg
