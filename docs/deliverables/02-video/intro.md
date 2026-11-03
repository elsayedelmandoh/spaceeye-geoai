# Intro video (Arabic narration, human and AI voice)

Task T-EL-26. Shown before the discussion with ACUD starts (1920x1080). Two versions with identical pictures and text cards, differing only in the voice:

- `intro-human-voice.mp4` (56 s): team recording `gamal-ramzy-cloned-voice.wav`; timing in `make/timing.json`.
- `intro-ai-voice.mp4` (51 s): AI voice `ai-voice-narration.wav` (Gemini 3.8 Flash TTS, voice Sulafat, via Renoise); timing in `make/timing-ai.json`.

Rebuild them with the kit in [`make/`](make/README.md): `python make/assemble.py make/out` (human) and `python make/assemble.py make/out make/timing-ai.json` (AI).

## Narration (Arabic, as spoken)

في العاصمة الجديدة، تُبنى مئاتُ المشروعات في الوقت نفسه. ولجنةُ المتابعة لا تستطيع أن تزور كلَّ مشروعٍ في كل دورة. فمن نزور أولاً؟ ولماذا؟
سبيس آي يقرأ صورَ الأقمار الصناعية كلَّ ربعِ سنة، ليرى أين يتحرك البناء، وأين توقف.
في الحي السكني السابع: اثنا عشر مشروعاً بأكواد، وأربعُ زياراتٍ في كل دورة.
القاعدة ترتّب الأولوية، وتشرح السبب بلغةٍ واضحة. والقرار يبقى للجنة.
سبيس آي: رادار العاصمة الجديدة - شركة تمتلك مدينة.

## Shots

Human-voice version (56 s):

| Time | Shot |
|---|---|
| 0:00-0:03.5 | Title card: SpaceEye GeoAI, "رادار العاصمة الجديدة: شركة تمتلك مدينة", supervisor and team credits |
| 0:03.5-0:10.4 | New city from the air (part 1: new capital, hundreds of projects) |
| 0:10.4-0:19.9 | A review team (part 2: the committee cannot visit all; whom first and why) |
| 0:19.9-0:30.0 | An observation satellite (part 3: satellite images every quarter) |
| 0:30.0-0:39.2 | A plot grid (part 4: R7, twelve coded projects, four visits per cycle) |
| 0:39.2-0:45.3 | A priority-coloured map (part 5, first sentence: the rule ranks and explains) |
| 0:45.3-0:48.0 | A committee table (part 5, last sentence: the committee decides) |
| 0:48.0-0:55.9 | End card with the project slogan "رادار العاصمة الجديدة: شركة تمتلك مدينة." (New Capital radar: a company that owns a city.) while it is spoken |

AI-voice version (51 s), same shots:

| Time | Shot |
|---|---|
| 0:00-0:03.5 | Title card |
| 0:03.5-0:08.5 | New city from the air (part 1) |
| 0:08.5-0:19.0 | A review team (part 2) |
| 0:19.0-0:27.2 | An observation satellite (part 3) |
| 0:27.2-0:35.0 | A plot grid (part 4) |
| 0:35.0-0:40.5 | A priority-coloured map (part 5, first sentence) |
| 0:40.5-0:43.2 | A committee table (part 5, last sentence) |
| 0:43.2-0:51.0 | End card with the project slogan |

Every cut is placed at the middle of a pause in the narration, so the picture changes as the spoken part changes.

## Chairman clips (inserted after the title card)

Three short excerpts of a public TV interview with Eng. Khaled Abbas, chairman of ACUD (YouTube `UlKa_Bh0twI`), play between the title card and the narration, each with a caption naming him and the source. Wording was checked against the video's Arabic captions.

| File | Interview time | Length | What he says |
|---|---|---|---|
| `khaled-abbas-1.mp4` | 25:29.3-25:35.4 | 6.1 s | About 500 real-estate developers and about 600 projects |
| `khaled-abbas-2.mp4` | 29:14.6-29:23.9 | 9.4 s | Asked how many are late: of the 500, no more than 7-8%, about 10-12 companies |
| `khaled-abbas-3.mp4` | 39:27.6-39:30.6 | 3.0 s | Data is the most important thing |

The clips add 18.5 s: `intro-human-voice.mp4` is 74.5 s and `intro-ai-voice.mp4` is 69.6 s. Every shot time in the tables above moves later by 18.5 s; narration and pictures move together, so each cut still lands on its narration pause. The kit adds them from the `inserts` list in `make/timing.json` and `make/timing-ai.json`.

These numbers are the chairman's spoken statements, not project measurements. The footage belongs to the broadcaster: the excerpts are for showing in the presentation with credit, not for publishing the edited video.

## Egypt Vision 2030 card

Before the end card the video shows a Vision 2030 card naming the two goals the project supports: goal 4, knowledge and innovation (geographic AI that reads satellite images), and goal 6, governance (field inspections directed by data with a known source). Goal 5 (environment) is left out because the project does not compute NDVI; it uses the Dynamic World vegetation share.

- `intro-human-voice.mp4` (80 s): the recorded narration cannot take new words, so the card is a silent 5.5 s beat between the last shot and the end card; everything after it moves together, so the slogan stays in sync.
- `intro-ai-voice.mp4` (75 s): for now it shows the same silent 5.5 s card. Planned next: a new AI narration that replaces "والقرار يبقى للجنة" with: "القاعدة ترتّب الأولوية وتشرح السبب، فتختصر على اللجنة وقتَ الزيارات، وتساعدها على اختيار زيارتها التالية ببياناتٍ معروفةِ المصدر. هكذا يخدم سبيس آي رؤيةَ مصر 2030 في الحوكمة والتحوّل الرقمي." The card will then be on screen while the Vision 2030 sentence is spoken (needs a new Renoise text-to-speech run).

## How it was made and what it is not

- Narration: the team-supplied recording gamal-ramzy-cloned-voice.wav (human version, 50.9 s) or ai-voice-narration.wav (AI version, 46.0 s); every cut is placed at a pause in the narration so the picture changes with the spoken part. Stills: Higgsfield `z_image`. A full video remake (480 Renoise credits; 35 Higgsfield credits per 5 s clip) was beyond the available balance.
- Assembled locally with ffmpeg (slow zooms, 0.5 s crossfades centred on each cut, fade from black); cards rendered in Chromium for correct Arabic shaping. Colors follow [`palette.md`](../01-presentation/palette.md).
- Partner logos stay on screen throughout: Digilians and ACUD top left, MCIT and the Egyptian Military Academy top right.
- The stills are AI-generated illustrations, not project satellite data, and do not show R7 or any coded compound. The end card says so.
- Every claim in the narration is in the deck: 12 coded R7 compounds, capacity 4 per cycle, quarterly satellite reading, the rule ranks and explains, the committee decides. "Hundreds of projects" follows the chairman statement on slide 1.
- No compound or developer names, no completion percentages, no generated numbers. The only names are the supervisor and team credits on the title card.
