// Builds docs/deliverables/01-presentation.pptx AND 01-presentation.md from one spec,
// so deck and markdown cannot drift. Run from the repo root: node .deck-build/build_pptx.js
const fs = require("fs");
const path = require("path");
const PptxGenJS = require("/home/aang/.claude/jobs/3f2c8eda/tmp/media/node_modules/pptxgenjs");

const REPO = process.cwd();
const C = { navy: "111111", sand: "FFFFFF", card: "F1F1F1", slate: "111111", orange: "E31B23", ink: "1A1A1A", text: "1A1A1A", white: "FFFFFF", red: "E31B23" };
const HEAD = "Cambria", BODY = "Calibri";
const MX = 0.6, W = 12.13, TOP = 1.4;
const SYN = "🟠 Synthetic - for training only";

const pres = new PptxGenJS();
pres.layout = "LAYOUT_WIDE";
pres.title = "SpaceEye committee presentation";

const warnings = [];
// Rough text-height estimate (Calibri ~0.5 em average glyph width); there is no renderer here.
function estH(text, pt, wIn) {
  const perLine = Math.max(1, Math.floor((wIn * 72) / (pt * 0.5)));
  return (Math.ceil(text.length / perLine) * pt * 1.2) / 72;
}
function check(label, texts, pt, wIn, hIn, gap = 0.08) {
  const need = texts.reduce((a, t) => a + estH(t, pt, wIn) + gap, 0) + 0.1;
  if (need > hIn) warnings.push(`${label}: needs ~${need.toFixed(2)}in, has ${hIn}in`);
}

// ---------- helpers (fresh option objects on every call) ----------
function base(slide, title, source, dark = false) {
  slide.background = { color: dark ? C.navy : C.sand };
  slide.addText(title, {
    x: MX, y: 0.4, w: W, h: 0.85, fontFace: HEAD, fontSize: 36, bold: true,
    color: dark ? C.white : C.text, align: "left", valign: "middle", margin: 0,
  });
  slide.addText("Source: " + source.join(" | ").replace(/`/g, ""), {
    x: MX, y: 6.5, w: W, h: 0.5, fontFace: BODY, fontSize: 10, color: dark ? C.card : C.red,
    align: "left", valign: "top", margin: 0,
  });
}
function bullets(slide, label, items, x, y, w, h, pt = 16, color = C.ink) {
  check(label, items, pt, w - 0.3, h);
  slide.addText(
    items.map((t) => ({ text: t, options: { bullet: true, breakLine: true, paraSpaceAfter: 6 } })),
    { x, y, w, h, fontFace: BODY, fontSize: pt, color, align: "left", valign: "top", margin: 0 }
  );
}
function stat(slide, label, x, y, w, h, big, cap) {
  slide.addShape(pres.ShapeType.rect, { x, y, w, h, fill: { color: C.card }, line: { color: C.card } });
  slide.addText(big, {
    x: x + 0.15, y: y + 0.1, w: w - 0.3, h: h * 0.45, fontFace: HEAD, fontSize: 36, bold: true,
    color: C.red, align: "left", valign: "middle", margin: 0, fit: "shrink",
  });
  check(label, [cap], 14, w - 0.3, h * 0.45);
  slide.addText(cap, {
    x: x + 0.15, y: y + h * 0.55, w: w - 0.3, h: h * 0.4, fontFace: BODY, fontSize: 14,
    color: C.ink, align: "left", valign: "top", margin: 0,
  });
}
function box(slide, label, x, y, w, h, text, o = {}) {
  slide.addShape(pres.ShapeType.rect, { x, y, w, h, fill: { color: o.fill || C.navy }, line: { color: o.fill || C.navy } });
  check(label, [text], o.pt || 14, w - 0.3, h);
  slide.addText(text, {
    x: x + 0.15, y: y + 0.08, w: w - 0.3, h: h - 0.16, fontFace: BODY, fontSize: o.pt || 14,
    color: C.white, align: "left", valign: "middle", margin: 0,
  });
}
function arrow(slide, x, y, w = 0.4, h = 0.4) {
  slide.addShape(pres.ShapeType.rightArrow, { x, y, w, h, fill: { color: C.red }, line: { color: C.red } });
}
function banner(slide, y = 1.35) {
  slide.addShape(pres.ShapeType.rect, { x: MX, y, w: 4.3, h: 0.42, fill: { color: C.orange }, line: { color: C.orange } });
  slide.addText(SYN, { x: MX + 0.15, y, w: 4.0, h: 0.42, fontFace: BODY, fontSize: 14, bold: true, color: C.white, align: "left", valign: "middle", margin: 0 });
}
function table(slide, label, rows, x, y, w, colW, pt = 14, rowH = 0.5, headFill = C.navy) {
  const cell = (t, head) => ({
    text: t,
    options: { fontFace: BODY, fontSize: pt, bold: !!head, color: head ? C.white : C.ink, align: "left", valign: "middle", fill: { color: head ? headFill : C.card } },
  });
  rows.forEach((r, ri) => r.forEach((t, ci) => { if (estH(t, pt, colW[ci] - 0.2) > rowH + 0.35) warnings.push(`${label} r${ri}c${ci} may wrap past row`); }));
  slide.addTable(rows.map((r, i) => r.map((t) => cell(t, i === 0))), { x, y, w, colW, rowH, border: { type: "solid", pt: 1, color: C.sand }, margin: [0.04, 0.1, 0.04, 0.1] });
}

// ---------- slide specs ----------
const slides = [];

// 1
slides.push({
  title: "Problem in numbers", time: "0:45",
  md: [
    "- 🟢 Real statement: More than 400 developers and more than 500 projects.",
    "- 🟢 Real statement: Field review every 3 months.",
    "- 🟢 Real statement: About 7-8% of developers seriously late; 6 mutual terminations.",
    "- A committee cannot visit everything every cycle: whom to visit first?",
    "- These are the chairman's statements, not our measurement.",
    "- Visual: five stat callouts (more than 400 developers · more than 500 projects · field review every 3 months · about 7-8% seriously late · 6 mutual terminations).",
  ],
  source: ["statements by the ACUD chairman, as recorded in `docs/requirements/01-specs.md` (section 12, slide 1)."],
  note: "Speaker note: 0:45 · criterion 1. A committee cannot visit everything every cycle, so the question is whom to visit first.",
  build(s) {
    const stats = [[">400", "developers"], [">500", "projects"], ["3 months", "between field reviews"], ["7-8%", "of developers seriously late"], ["6", "mutual terminations"]];
    const w = (W - 4 * 0.2) / 5;
    stats.forEach(([b, c], i) => stat(s, "s1 stat " + i, MX + i * (w + 0.2), TOP + 0.2, w, 1.9, b, c));
    bullets(s, "s1 bullets", [
      "A committee cannot visit everything every cycle: whom to visit first?",
      "These are the chairman's statements, not our measurement.",
    ], MX, 3.9, W, 1.8, 18);
  },
});

// 2
slides.push({
  title: "The question and the decision", time: "0:45",
  md: [
    "- Question: which R7 compounds should the committee visit first next cycle, and why?",
    "- The observatory ranks; the committee decides.",
    "- Scope: R7 only, 12 coded compounds, reporting quarter 2026Q3, cycle capacity 4.",
    "- As-is → to-be: today every one of the 12 compounds gets a field review every 3 months (4 visits a year each); tomorrow a cycle list of at most 4 compounds from levels 1-3, each with a reason sentence, and the committee decides.",
    "- ACUD has not given us visit times or missed cases, so the as-is pain is not measured.",
    "- Visual: as-is → to-be flow of two boxes.",
  ],
  source: ["`configs/cost_assumptions.yaml` (`projects: 12`, `visits_per_year: 4`), `docs/requirements/01-specs.md` (sections 2, 7 and 12)."],
  note: "Speaker note: 0:45 · criteria 1, 2, 3. One sentence from today's practice to the new list; the decision itself comes on slide 11.",
  build(s) {
    const bw = 5.5;
    box(s, "s2 asis", MX, TOP + 0.1, bw, 1.7, "Today (as-is): every one of the 12 compounds gets a field review every 3 months, 4 visits a year each.", { fill: C.slate, pt: 16 });
    arrow(s, MX + bw + 0.3, TOP + 0.75, 0.5, 0.5);
    box(s, "s2 tobe", MX + bw + 1.1, TOP + 0.1, bw + 0.03, 1.7, "Tomorrow (to-be): a cycle list of at most 4 compounds from levels 1-3, each with a reason sentence. The committee decides.", { fill: C.red, pt: 16 });
    bullets(s, "s2 bullets", [
      "Question: which R7 compounds should the committee visit first next cycle, and why?",
      "The observatory ranks; the committee decides.",
      "Scope: R7 only, 12 coded compounds, reporting quarter 2026Q3, cycle capacity 4.",
      "ACUD has not given us visit times or missed cases, so the as-is pain is not measured.",
    ], MX, 3.5, W, 2.9, 18);
  },
});

// 3
slides.push({
  title: "Data", time: "0:45",
  md: [
    "- 1,009 of 1,026 documented facts passed independent review. This is the figure stated in the spec, not a recount.",
    "- Origin key on every number: 🟢 real, 🔵 derived, 🟠 generated.",
    "- Real: satellite series, statements, laws. Generated: finance, supervisor reports, meters, complaints (only ACUD holds the real ones).",
    "- Visual: stat callout (1,009 of 1,026) and origin-key table.",
  ],
  source: ["`docs/requirements/01-specs.md` (section 12); `data/DATASET_CONTRACT.md` (tables)."],
  note: "Speaker note: 0:45 · criteria 2, 8. Point to the origin key; it is used on every later slide. The installed data has no facts register, so 1,009 of 1,026 is the figure stated in the spec (section 12), not a recount; the dashboard's data-trust screen shows the same documented figure.",
  build(s) {
    stat(s, "s3 stat", MX, TOP + 0.1, 3.9, 2.2, "1,009 of 1,026", "documented facts passed independent review");
    table(s, "s3 table", [
      ["Origin", "Contents"],
      ["🟢 Real", "Satellite series, statements, laws"],
      ["🔵 Derived", "Computed from the real inputs"],
      ["🟠 Generated", "Finance, supervisor reports, meters, complaints (only ACUD holds the real ones)"],
    ], MX + 4.2, TOP + 0.1, W - 4.2, [2.0, W - 4.2 - 2.0], 14, 0.55);
    bullets(s, "s3 bullets", [
      "The figure is the one stated in the spec, not a recount.",
      "The origin key (🟢 🔵 🟠) is on every later number.",
    ], MX, 3.9, W, 1.8, 18);
  },
});

// 4
slides.push({
  title: "Seeing construction from space", time: "0:30",
  md: [
    "- Dynamic World gives a quarterly built probability per compound; the activity score A is the probability that the compound is building this quarter.",
    "- Open Buildings gives yearly heights to 2023; approved height context extends through 2024 and is shown only as context, never part of a priority level.",
    "- Wayback before/after images (with capture date and attribution) are for display; Esri terms to be confirmed before use.",
    "- A quarter is assessable only with at least 6 Dynamic World images and a boundary with a reviewed confidence label (K4).",
    "- Limit: satellites show whether building is happening, not interior finishing. No completion % or finishing % is given.",
    "- Visual: three-row source table (source · gives · role).",
  ],
  source: ["`docs/requirements/01-specs.md` and `data/DATASET_CONTRACT.md`."],
  note: "Speaker note: 0:30 · criteria 2, 6. Say what the satellite sees and what it cannot.",
  build(s) {
    table(s, "s4 table", [
      ["Source", "Gives", "Role"],
      ["Dynamic World", "Quarterly built probability; activity score A", "Measures activity"],
      ["Open Buildings", "Yearly heights to 2023; approved context through 2024", "Context only, never part of a level"],
      ["Wayback images", "Before/after with capture date and attribution", "Display only; Esri terms to be confirmed"],
    ], MX, TOP + 0.1, W, [2.4, 5.2, W - 7.6], 14, 0.6);
    bullets(s, "s4 bullets", [
      "A quarter is assessable only with at least 6 Dynamic World images and a boundary with a reviewed confidence label (K4).",
      "Limit: satellites show whether building is happening, not interior finishing. No completion % or finishing % is given.",
    ], MX, 4.2, W, 2.1, 18);
  },
});

// 5
slides.push({
  title: "The Track A rule", time: "1:00",
  md: [
    "- Priority level = the worst of K2 (quarters with no activity after construction started), K3 (months since the first announced handover date) and K6 (months since the first launch or promise with no confirmed start). No weights.",
    "- Cap: if a handover is announced or vegetation share is 0.10 or more, the level is at most 3 (in 2026Q3 this sets 3 of 12 levels: C03, C12 and C21).",
    "- Level 1 inspect now; level 2 inspect this cycle; level 3 document review; level 4 routine. Follow-up states without a level: not started, start unknown, not assessable.",
    "- Legal references: 12 months handover grace and 24 months right to refund (Decree 2184/2022).",
    "- K5 (fine-eligible months) is illustrative and never sets a level.",
    "- Plan gap B5 (planned minus reported progress) is generated data (🟠) and appears only in Track B.",
    "- Visual: rule flow (K2, K3, K6 → worst signal → cap) and level-action table.",
  ],
  source: ["`docs/deliverables/kpi-cards.md` (cap count), `configs/data.yaml`, `docs/requirements/01-specs.md` (level table: 24 months right to refund)."],
  note: "Speaker note: 1:00 · criteria 3, 4. The worst signal sets the level, without weights, and each level maps to an action.",
  build(s) {
    const kw = 2.45, y = TOP + 0.05, h = 1.15;
    [["K2", "Quarters with no activity after construction started"], ["K3", "Months since the first announced handover date"], ["K6", "Months since first launch or promise, no confirmed start"]].forEach(([k, t], i) =>
      box(s, "s5 " + k, MX + i * (kw + 0.12), y, kw, h, k + ": " + t, { pt: 14 }));
    arrow(s, MX + 3 * (kw + 0.12), y + 0.4, 0.4, 0.4);
    box(s, "s5 worst", MX + 3 * (kw + 0.12) + 0.5, y, W - (3 * (kw + 0.12) + 0.5), h, "Worst signal sets the level (no weights); a \"may be complete\" cap holds it at 3 or less", { fill: C.red, pt: 14 });
    table(s, "s5 table", [
      ["Level", "Action"],
      ["1", "Inspect now"],
      ["2", "Inspect this cycle"],
      ["3", "Document review"],
      ["4", "Routine"],
    ], MX, 2.85, 4.4, [1.2, 3.2], 14, 0.5);
    bullets(s, "s5 bullets", [
      "Cap: handover announced or vegetation share 0.10 or more → level at most 3 (2026Q3: 3 of 12 levels: C03, C12, C21).",
      "Without a level: not started, start unknown, not assessable.",
      "Legal references: 12 months handover grace, 24 months right to refund (Decree 2184/2022).",
      "K5 (fine-eligible months) is illustrative and never sets a level.",
      "Plan gap B5 is generated (🟠) and appears only in Track B.",
    ], MX + 4.7, 2.85, W - 4.7, 3.55, 14);
  },
});

// 6
slides.push({
  title: "Live demo (Track A)", time: "1:30",
  md: [
    "- Priority map, cycle list (capacity 4, levels 1-3), open one compound, read its reason sentence, open the inspection file, record a visit result.",
    "- Everything on screen in Track A is real or derived. No generated number appears on the map.",
    "- Dependency: the demo needs the dashboard to run from stored files. Run command: `make run (team_run --full, which calls run_all)`, the one run command per board task T-AH-19.",
    "- Visual: five-step flow (priority map → cycle list → reason sentence → inspection file → visit result).",
  ],
  source: ["`docs/deliverables/user-guide.md`; board task T-AH-19 in `docs/requirements/02-team-roles-and-tasks.md`."],
  note: "Speaker note: 1:30 · criterion 4. Follow the alert to the action: level, cycle list, inspection file, visit form.",
  build(s) {
    const steps = ["Priority map", "Cycle list (capacity 4, levels 1-3)", "Compound reason sentence", "Inspection file", "Visit result recorded"];
    const bw = 1.95, gap = (W - 5 * bw) / 4;
    steps.forEach((t, i) => {
      box(s, "s6 step " + i, MX + i * (bw + gap), TOP + 0.2, bw, 1.5, t, { fill: i === 4 ? C.red : C.navy, pt: 16 });
      if (i < 4) arrow(s, MX + i * (bw + gap) + bw + (gap - 0.3) / 2, TOP + 0.75, 0.3, 0.4);
    });
    bullets(s, "s6 bullets", [
      "Everything on screen in Track A is real or derived. No generated number appears on the map.",
      "Dependency: the dashboard runs from stored files. Run command: make run (team_run --full, which calls run_all), the one run command per board task T-AH-19.",
    ], MX, 3.6, W, 2.7, 18);
  },
});

// 7
slides.push({
  title: "Backtest: 1 of 6 and why", time: "1:45",
  md: [
    "- Six public R7 cases, checked with the clock frozen. Codes only, even on this slide.",
    "- Early alert in 1 of 6 cases (after-start reading, case C21) and 0 of 6 (point-in-time reading).",
    "- The target of 5 cases was fixed before computing, was not lowered and was not met.",
    "- Imaging was sufficient in every case (at least 10 images per quarter). In the five missed cases the sites were seen as active, so the rule had no stall to detect. The rule measures stalls and passed dates, not pace against plan.",
    "- The one hit (C21) came from a start date set by publication timing and a lag in the activity score, not from a real stall during construction, so it does not carry over to the other five.",
    "- These counts do not prove why each delay happened.",
    "- Visual: three stat callouts (1 of 6 · 0 of 6 · 5 required, not achieved).",
  ],
  source: ["`data/BACKTEST_CURRENT.md`, `data/experiments/35_backtest_diagnosis/DIAGNOSIS.md`."],
  note: "Speaker note: 1:45 · criterion 6. Lead with the miss, and say the target was fixed before computing.",
  build(s) {
    const w = (W - 0.4) / 3;
    stat(s, "s7 a", MX, TOP + 0.05, w, 1.45, "1 of 6", "early alert, after-start reading (C21)");
    stat(s, "s7 b", MX + w + 0.2, TOP + 0.05, w, 1.45, "0 of 6", "early alert, point-in-time reading");
    stat(s, "s7 c", MX + 2 * (w + 0.2), TOP + 0.05, w, 1.45, "5 required", "fixed before computing; not lowered, not achieved");
    bullets(s, "s7 bullets", [
      "Six public R7 cases, checked with the clock frozen. Codes only.",
      "Imaging was sufficient in every case (at least 10 images per quarter). In the five misses the sites looked active, so the rule had no stall to detect. The rule measures stalls and passed dates, not pace against plan.",
      "The one hit (C21) came from a start date set by publication timing and a lag in the activity score, not a real stall; it does not carry over to the other five.",
      "These counts do not prove why each delay happened.",
    ], MX, 3.15, W, 3.25, 16);
  },
});

// 8
const RECALL = [["Public rule", 3], ["Combined rule", 3], ["Logistic, satellite", 1], ["Logistic, combined", 2], ["Boosting, satellite", 4], ["Boosting, combined", 1]];
slides.push({
  title: "Track B: generated data", time: "1:00",
  md: [
    "- 🟠 Synthetic - for training only.",
    "- Scope: R7, 12 coded compounds. Target: distressed / not_distressed in the next six months. Completion prediction is outside the approved scope.",
    "- Data: 96 training rows and 48 test rows. The test holds only 4 distressed rows, so statistical power is very low.",
    "- Recall@4 (distressed cases among the top 4 of the list; denominator 4), on generated data: " + RECALL.map(([n, v]) => `${n.toLowerCase()} ${v} of 4`).join("; ") + ".",
    "- Caveat: the boosting 4 of 4 rests partly on the height column; the v2a run without height gives 1 of 4 (`data/EW_V2A_VS_V1.md`).",
    "- Baseline: random top-4 list, 2,000 draws, mean 0.335, 95% interval 0.000 to 0.750.",
    "- Reading: with 4 cases the methods cannot be separated, and combining ACUD-style data did not clearly help. Scores are diagnostic and do not show real-world accuracy.",
    "- Visual: native bar chart of recall@4 for the six methods.",
  ],
  source: ["`docs/deliverables/complaints_eval.csv`, `data/EW_V2A_VS_V1.md`."],
  note: "Speaker note: 1:00 · criterion 6. Generated data only; with 4 test cases the methods cannot be separated. For questions, complaints classifier: the keyword baseline scored 0.27 accuracy on the 104-row benchmark and 0.37 on the 30-item check set; TF-IDF plus logistic scored 0.22 and 0.30, respectively. Accuracy on texts written by the team does not prove accuracy on real complaints.",
  build(s) {
    banner(s);
    bullets(s, "s8 bullets", [
      "Target: distressed / not_distressed in the next six months. Completion prediction is out of scope.",
      "96 training rows, 48 test rows; only 4 test rows are distressed, so power is very low.",
      "Boosting 4 of 4 rests partly on height; without height (v2a) it is 1 of 4.",
      "Random top-4 baseline: mean 0.335, 95% interval 0.000 to 0.750 (2,000 draws).",
      "With 4 cases the methods cannot be separated. Scores are diagnostic, not real-world accuracy.",
    ], MX, 1.95, 5.5, 4.45, 14);
    s.addChart(pres.charts.BAR, [{ name: "Recall@4 (of 4)", labels: RECALL.map((r) => r[0]), values: RECALL.map((r) => r[1]) }], {
      x: 6.4, y: 1.95, w: 6.33, h: 4.45, barDir: "col", chartColors: [C.orange], showLegend: false,
      showValue: true, dataLabelFontSize: 14, dataLabelColor: C.ink, valAxisMinVal: 0, valAxisMaxVal: 4, valAxisMajorUnit: 1,
      valAxisLabelFontSize: 12, catAxisLabelFontSize: 11, catAxisLabelFontFace: BODY, valAxisLabelFontFace: BODY,
      showTitle: true, title: "Recall@4 on generated data (distressed cases in top 4, of 4)", titleFontSize: 13, titleFontFace: BODY, titleColor: C.ink,
      valGridLine: { color: C.card, size: 0.75 }, catGridLine: { style: "none" },
    });
  },
});

// 8b
slides.push({
  title: "The observatory: one what-if scenario", time: "0:30",
  md: [
    "- 🟠 Synthetic - for training only.",
    "- Light compound-level observatory: observed state from satellites and statements, simulated hidden state from the generator, what-if scenarios.",
    "- Scenarios: S1 dollar shock, S2 collections drop, S3 inspection capacity change. Demo S3 live: who enters or leaves the cycle list at 2 or 6 visits instead of 4 (45 of 744 rows change list membership: 28 at capacity 2, 17 at capacity 6; levels never change).",
    "- S1 and S2 change nothing in the list or the levels (0 of 216 rows each).",
    "- Generated (🟠), orange banner on screen, no map. Not a 3D or real-time observatory.",
    "- Visual: scenario table (S1 · S2 · S3 and rows changed).",
  ],
  source: ["`logs/review-05.md` (scenario row counts)."],
  note: "Speaker note: 0:30 · criterion 6. Show S3 only; say S1 and S2 change nothing.",
  build(s) {
    banner(s);
    table(s, "s8b table", [
      ["Scenario", "What changes", "Rows that change list membership"],
      ["S1", "Dollar shock", "0 of 216; levels never change"],
      ["S2", "Collections drop", "0 of 216; levels never change"],
      ["S3", "Inspection capacity 2 or 6 instead of 4", "45 of 744 (28 at capacity 2, 17 at capacity 6); levels never change"],
    ], MX, 2.0, W, [1.6, 4.0, W - 5.6], 14, 0.6, C.orange);
    bullets(s, "s8b bullets", [
      "Light compound-level observatory: observed state from satellites and statements, simulated hidden state from the generator, what-if scenarios.",
      "Demo S3 live. Say plainly that S1 and S2 change nothing in the list or levels.",
      "Orange banner on screen, no map. Not a 3D or real-time observatory.",
    ], MX, 4.7, W, 1.7, 16);
  },
});

// 9
slides.push({
  title: "Value in EGP (3 settings)", time: "1:45",
  md: [
    "- Visiting 4 compounds per cycle instead of all 12: 16 visits a year instead of visiting every compound each cycle.",
    "- Under these assumptions, from -0.006 to 0.098 million EGP per year.",
    "- Every cost input is an assumption. The conservative setting is negative.",
    "- Cost per visit (2,000 / 3,000 / 4,000 EGP) is an assumption based on a team of 3 at published engineer pay plus assumed transport. Operating cost, missed cases and cost of a late case are placeholders.",
    "- The cost of a false alarm against the cost of a missed case has not been measured.",
    "- Not a measured saving.",
    "- Visual: two stat callouts (-0.006 and 0.098 million EGP per year) and a three-setting table (cost per visit, operating cost, missed cases per year).",
  ],
  source: ["`configs/cost_assumptions.yaml` (the same file holds the three settings and the placeholder values); `docs/deliverables/rubric-map.md` (criterion 6 gap)."],
  note: "Speaker note: 1:45 · criterion 7. Compare with the current policy of visiting all 12; say the conservative setting is negative. The cost of a late case is a placeholder of 20,000 EGP per missed case in all three settings.",
  build(s) {
    stat(s, "s9 lo", MX, TOP + 0.05, 3.0, 1.9, "-0.006", "million EGP per year, low end");
    stat(s, "s9 hi", MX + 3.2, TOP + 0.05, 3.0, 1.9, "0.098", "million EGP per year, high end");
    table(s, "s9 table", [
      ["Setting", "Cost per visit (EGP)", "Operating cost (EGP/yr, placeholder)", "Missed cases per year (placeholder)"],
      ["Conservative", "2,000", "30,000", "2"],
      ["Central", "3,000", "20,000", "1"],
      ["Optimistic", "4,000", "10,000", "1"],
    ], MX + 6.6, TOP + 0.05, W - 6.6, [1.35, 1.2, 1.5, W - 6.6 - 4.05], 12, 0.5);
    bullets(s, "s9 bullets", [
      "Visiting 4 compounds per cycle instead of all 12: 16 visits a year.",
      "Every cost input is an assumption; the conservative setting is negative. Not a measured saving.",
      "Cost per visit (assumption): a team of 3 at published engineer pay plus assumed transport. Operating cost, missed cases and cost of a late case are placeholders.",
      "The cost of a false alarm against the cost of a missed case has not been measured.",
    ], MX, 3.6, W, 2.8, 16);
  },
});

// 10
const RISKS = [
  ["A level is not a finding", "It says whom to visit first; it is not misconduct, legal distress, breach or a verified fine. No automatic sanction."],
  ["Unknown stays unknown", "Missing evidence is never read as negative. K3 relies on developer statements, not independent measurement."],
  ["Generated data", "Never mixed with real data; Track B is marked and hidden from the map. It shows nothing about real accuracy or fairness."],
  ["Small samples", "6 real cases and 4 test cases: counts only, no percentages."],
  ["Complaint text", "Masking does not prove every real name is removed; real text needs further review. No external AI call is enabled."],
  ["Law 151/2020", "Interpretation needs the data custodian's review. Not legal advice."],
  ["Handover", "Guides, method card and checklist are in the repo; no one outside the team has rebuilt the system from them yet."],
];
slides.push({
  title: "Risks and responsible use", time: "1:00",
  md: [
    ...RISKS.map(([a, b]) => `- ${a}: ${b}`),
    "- The committee decides; every visit result is recorded to build real ground truth.",
    "- Knowledge transfer: technical operations guide, committee user guide, handover pack, method card and final checklist are in the repo; the user guide was checked against the code, not in a browser.",
    "- Visual: risk and control table.",
  ],
  source: ["`docs/deliverables/responsible-ai.md`, `docs/requirements/01-specs.md` (Law 151/2020).", "(knowledge transfer) `docs/deliverables/technical-track-a.md`, `docs/deliverables/user-guide.md`, `docs/deliverables/knowledge-transfer.md`, `docs/deliverables/method-card.md`, `docs/deliverables/final-checklist.md`."],
  note: "Speaker note: 1:00 · criteria 8, 9. A level sets the visit order and finds nothing against anyone. Then give one line on the handover documents. The committee decides, and every visit result is recorded to build real ground truth. The user guide was checked against the code, not in a browser.",
  build(s) {
    table(s, "s10 table", [["Topic", "Rule or limit"], ...RISKS], MX, TOP, W, [2.7, W - 2.7], 14, 0.58);
  },
});

// 11
const PH = [
  ["1 · Pilot cycle", "Run one cycle with the list; record every visit result.", "Committee decides; Track A owner prepares the list.", "Little ground truth; no accuracy claim.", "The current 3-month review continues."],
  ["2 · ACUD data", "Coded export ordered by impact; small verified sample first.", "ACUD data custodian keeps the identity mapping.", "Access and approval not yet given.", "Stay on public data; missing stays unknown."],
  ["3 · Quarterly operation", "Quarterly monitoring; thresholds and capacity change only by reviewed decision.", "Proposed: Track A owner operates, another team member reviews.", "Activity score A fails on new quarters.", "Fall back to K1; prior releases stay available."],
];
slides.push({
  title: "Decision, transition and next step", time: "0:45", dark: true,
  md: [
    "- **Decision requested:** use the inspection priority list to choose which R7 compounds the committee visits first next cycle. The system recommends; the committee decides.",
    "- Message: this is what public data alone can do. Give us your data and the demo parts become real operation.",
    "- Transition roadmap (phase · what · owner role · risk · rollback):",
    ...PH.map(([t, d, o, r, b]) => `  - Phase ${t}: ${d} Owner: ${o} Risk: ${r} Rollback: ${b}`),
    "- Training of committee users, dates, phase-gate criteria and signed owners: to be agreed with ACUD.",
    "- Transfer: thresholds and capacity are configuration; another region needs its boundaries and statements. Only R7 has been run; no transfer is proven.",
    "- Next step: run one cycle with the list and record visit results.",
    "- Visual: decision box and three-phase roadmap.",
  ],
  source: ["`docs/deliverables/decision-memo.md` (decision requested), `docs/deliverables/data-request.md`, `docs/requirements/01-specs.md` (data request list, art. 54; section 13 risks and fallbacks), `docs/deliverables/technical-track-a.md` (quarterly monitoring procedure)."],
  note: "Speaker note: 0:45 · criteria 5, 10, bonus. Open with the decision, name the first phase and close on the next step. Total 12:00. For questions: the ACUD export is ordered by impact (dated inspection and handover outcomes, contract register, parcel geometry first); any STOP in the monitoring procedure writes no manifest.",
  build(s) {
    s.addShape(pres.ShapeType.rect, { x: MX, y: TOP, w: W, h: 0.95, fill: { color: C.sand }, line: { color: C.sand } });
    const dec = "Decision requested: use the inspection priority list to choose which R7 compounds the committee visits first next cycle. The system recommends; the committee decides.";
    check("s11 decision", [dec], 18, W - 0.4, 0.95);
    s.addText(dec, { x: MX + 0.2, y: TOP + 0.05, w: W - 0.4, h: 0.85, fontFace: BODY, fontSize: 18, bold: true, color: C.text, align: "left", valign: "middle", margin: 0 });
    const pw = (W - 0.3) / 3;
    PH.forEach(([t, d, o, r, b], i) => {
      const x = MX + i * (pw + 0.15), y = TOP + 1.1, h = 2.5;
      s.addShape(pres.ShapeType.rect, { x, y, w: pw, h, fill: { color: C.card }, line: { color: C.card } });
      const runs = [
        { text: "Phase " + t, options: { bold: true, fontFace: HEAD, fontSize: 16, color: C.text, breakLine: true } },
        { text: d, options: { breakLine: true } },
        { text: "Owner: " + o, options: { breakLine: true } },
        { text: "Risk: " + r, options: { breakLine: true } },
        { text: "Rollback: " + b, options: {} },
      ].map((r2) => ({ text: r2.text, options: { fontFace: BODY, fontSize: 14, color: C.ink, paraSpaceAfter: 4, ...r2.options } }));
      check("s11 phase " + i, [t, d, "Owner: " + o, "Risk: " + r, "Rollback: " + b], 14, pw - 0.3, h);
      s.addText(runs, { x: x + 0.15, y: y + 0.1, w: pw - 0.3, h: h - 0.2, align: "left", valign: "top", margin: 0 });
    });
    bullets(s, "s11 bullets", [
      "Message: this is what public data alone can do. Give us your data and the demo parts become real operation.",
      "Training, dates, phase-gate criteria and signed owners: to be agreed with ACUD. Only R7 has been run; no transfer is proven.",
      "Next step: run one cycle with the list and record visit results.",
    ], MX, 5.3, W, 1.15, 13, C.white);
  },
});

// ---------- build ----------
slides.forEach((sp) => {
  const s = pres.addSlide();
  base(s, sp.title, sp.source, !!sp.dark);
  sp.build(s);
  s.addNotes(sp.note);
});

// ---------- markdown ----------
const labels = ["1", "2", "3", "4", "5", "6", "7", "8", "8b", "9", "10", "11"];
const md = [
  "# Presentation: 12 slides (numbered 1-11, with 8b after 8)",
  "",
  "Tasks T-SA-06 and T-EL-25. Draft text for review. This file holds the on-slide content and speaker notes of `01-presentation.pptx`, slide for slide in the same order. Length: 12 min, the limit set by criterion 10 of the instructor rubric (`docs/requirements/ACUD-Rubric.md`); the time budget and the criteria each slide answers follow `docs/deliverables/rubric-map.md` (presentation plan) and are stated in each speaker note (total 12:00). Numbers come only from repo files and carry an origin mark: 🟢 real · 🔵 derived · 🟠 generated (\"Synthetic - for training only\"). Codes only, no names. The words \"risk level\", \"distressed\" (for a real compound) and any completion % are not used. Some caveats are in the speaker notes.",
  "",
];
slides.forEach((sp, i) => {
  md.push(`## Slide ${labels[i]}. ${sp.title}`, "", ...sp.md);
  sp.source.forEach((src) => md.push(`- Source${src.startsWith("(knowledge transfer)") ? " (knowledge transfer)" : ""}: ${src.replace("(knowledge transfer) ", "")}`));
  md.push("", sp.note, "");
});
const secs = slides.reduce((a, sp) => { const [m, s2] = sp.time.split(":").map(Number); return a + m * 60 + s2; }, 0);
if (secs !== 720) warnings.push("total time is " + secs + "s, not 720");
slides.forEach((sp) => { if (!sp.note.startsWith("Speaker note: " + sp.time)) warnings.push("note time mismatch: " + sp.title); });

fs.writeFileSync(path.join(REPO, "docs/deliverables/01-presentation.md"), md.join("\n"));
pres.writeFile({ fileName: path.join(REPO, "docs/deliverables/01-presentation.pptx") }).then(() => {
  console.log("slides:", slides.length, "warnings:", warnings.length);
  warnings.forEach((w) => console.log("WARN", w));
});
