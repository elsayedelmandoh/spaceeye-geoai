// Builds presentation.pptx AND presentation.md (both in docs/deliverables/01-presentation/) from one spec,
// so deck and markdown cannot drift. Run from the repo root: node make/build_pptx.js
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

// ---------- logos (aspect ratios from the PNG pixel sizes) ----------
const LOGO_ACUD = path.join(__dirname, "..", "..", "02-video", "logo-ACUD.png");     // 400x207, drawn mark 171 px high
const LOGO_DIG = path.join(__dirname, "..", "..", "02-video", "logo-digilians.png"); // 500x500, drawn mark 321 px high (white margins)
const ACUD_AR = 400 / 207;
const DIG_SCALE = (171 / 207) * (500 / 321); // Digilians image height per ACUD image height, so the drawn marks match
function logos(slide, acudH, rightX, cy, gap) {
  const digH = acudH * DIG_SCALE, acudW = acudH * ACUD_AR;
  const x0 = rightX - (acudW + gap + digH);
  slide.addImage({ path: LOGO_ACUD, x: x0, y: cy - acudH / 2, w: acudW, h: acudH });
  slide.addImage({ path: LOGO_DIG, x: x0 + acudW + gap, y: cy - digH / 2, w: digH, h: digH });
}
const LOGO_H_SMALL = 0.5, LOGO_GAP_SMALL = 0.1;
const LOGO_BLOCK_W = LOGO_H_SMALL * ACUD_AR + LOGO_GAP_SMALL + LOGO_H_SMALL * DIG_SCALE;

// ---------- helpers (fresh option objects on every call) ----------
function base(slide, title, source, dark = false) {
  slide.background = { color: dark ? C.navy : C.sand };
  const logoX = MX + W - LOGO_BLOCK_W;
  if (dark) slide.addShape(pres.ShapeType.roundRect, { x: logoX - 0.1, y: 0.35, w: LOGO_BLOCK_W + 0.2, h: 0.8, rectRadius: 0.1, fill: { color: C.white }, line: { color: C.white } });
  logos(slide, LOGO_H_SMALL, MX + W, 0.75, LOGO_GAP_SMALL);
  slide.addText(title, {
    x: MX, y: 0.4, w: logoX - 0.2 - MX, h: 0.85, fontFace: HEAD, fontSize: 36, bold: true,
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

// Dashboard screenshots (1600x950 PNGs in assets/). crop = region in source pixels; aspect ratio is kept.
const SHOTS = {
  search: { file: "screen1-search-filters.png", name: "Priority map, search and filters" },
  chatbot: { file: "chatbot-home.png", name: "Chatbot, start screen" },
  top: { file: "screen1-top.png", name: "Priority map" },
  mapPanel: { file: "screen1-map-panel.png", name: "Priority map, selected compound" },
  file: { file: "screen2-compound-file.png", name: "Compound file" },
  district: { file: "screen3-district-view.png", name: "District view" },
  twin: { file: "screen4-twin-what-if.png", name: "Digital twin what if", crop: { x: 400, y: 340, w: 1100, h: 205 } },
};
function shot(slide, key, x, y, w) {
  const sh = SHOTS[key], cw = sh.crop ? sh.crop.w : 1600, ch = sh.crop ? sh.crop.h : 950, k = w / cw, h = ch * k;
  const o = { path: path.join(__dirname, "..", "assets", sh.file), x, y, w: 1600 * k, h: 950 * k };
  if (sh.crop) o.sizing = { type: "crop", x: sh.crop.x * k, y: sh.crop.y * k, w, h };
  slide.addImage(o);
  slide.addShape(pres.ShapeType.rect, { x, y, w, h, fill: { type: "none" }, line: { color: C.slate, width: 0.75 } });
  slide.addText("Dashboard screenshot · " + sh.name, { x, y: y + h + 0.03, w, h: 0.22, fontFace: BODY, fontSize: 11, italic: true, color: C.ink, align: "left", valign: "top", margin: 0 });
  return h;
}
const shotMd = (keys) => keys.map((k) => `- Screenshot: \`assets/${SHOTS[k].file}\`, "Dashboard screenshot · ${SHOTS[k].name}".`);

// ---------- slide specs ----------
const slides = [];

// 0 (title slide)
slides.push({
  cover: true,
  title: "SpaceEye GeoAI", time: "0:15",
  md: [
    "- SpaceEye GeoAI",
    "- New Capital Radar: a company that owns a city.",
    "- Supervisor: Dr. Nadim Abdin - Partner & VP Business Development",
    "- Team: Elsayed Elmandoh, Verina Fouad, Ahmed Abdelhameed, Nada Shady, Salma Magdy",
  ],
  source: [],
  note: "Speaker note: 0:15 · opening. Name the project and the slogan, thank the supervisor, introduce the team in one line.",
  build(s) {
    logos(s, 1.0, MX + W / 2 + (ACUD_AR + 0.3 + DIG_SCALE) / 2, 0.95, 0.3);
    s.addText("SpaceEye GeoAI", { x: MX, y: 1.7, w: W, h: 1.2, fontFace: HEAD, fontSize: 54, bold: true, color: C.text, align: "center", valign: "middle", margin: 0 });
    s.addShape(pres.ShapeType.rect, { x: MX + W / 2 - 1.6, y: 3.0, w: 3.2, h: 0.08, fill: { color: C.red }, line: { color: C.red } });
    s.addText("New Capital Radar: a company that owns a city.", { x: MX, y: 3.25, w: W, h: 0.8, fontFace: HEAD, fontSize: 28, color: C.red, align: "center", valign: "middle", margin: 0 });
    s.addText([
      { text: "Supervisor: Dr. Nadim Abdin - Partner & VP Business Development", options: { breakLine: true } },
      { text: "Team: Elsayed Elmandoh, Verina Fouad, Ahmed Abdelhameed, Nada Shady, Salma Magdy" },
    ], { x: MX, y: 4.5, w: W, h: 1.2, fontFace: BODY, fontSize: 18, color: C.text, align: "center", valign: "middle", margin: 0, paraSpaceAfter: 6 });
  },
});

// 1
slides.push({
  title: "Problem in numbers", time: "0:30",
  md: [
    "- 🟢 Real statement: More than 400 developers and more than 500 projects.",
    "- 🟢 Real statement: Field review every 3 months.",
    "- 🟢 Real statement: About 7-8% of developers seriously late; 6 mutual terminations.",
    "- A committee cannot visit everything every cycle: whom to visit first?",
    "- These are the chairman's statements, not our measurement.",
    "- The gap: with more than 500 projects and a review every 3 months, the open question is which compounds come first. ACUD's data (plot boundaries, handover dates, supervisor reports, field review records) is what would turn our public-data screening into operation.",
    "- Visual: gap graphic (more than 500 projects, review every 3 months → which compounds first? → a short cycle list), five stat callouts (more than 400 developers · more than 500 projects · field review every 3 months · about 7-8% seriously late · 6 mutual terminations).",
  ],
  source: ["statements by the ACUD chairman, as recorded in `docs/requirements/01-specs.md` (section 12, slide 1 and the data request list)."],
  note: "Speaker note: 0:30 · criterion 1. A committee cannot visit everything every cycle, so the question is whom to visit first.",
  build(s) {
    const stats = [[">400", "developers"], [">500", "projects"], ["3 months", "between field reviews"], ["7-8%", "of developers seriously late"], ["6", "mutual terminations"]];
    const w = (W - 4 * 0.2) / 5;
    stats.forEach(([b, c], i) => stat(s, "s1 stat " + i, MX + i * (w + 0.2), TOP + 0.2, w, 1.9, b, c));
    box(s, "s1 g1", MX, 3.75, 4.6, 0.95, "More than 500 projects, and a field review every 3 months", { fill: C.slate, pt: 16 });
    arrow(s, MX + 4.75, 4.0, 0.45, 0.45);
    box(s, "s1 g2", MX + 5.35, 3.75, 3.3, 0.95, "Which compounds come first?", { fill: C.red, pt: 16 });
    arrow(s, MX + 8.8, 4.0, 0.45, 0.45);
    box(s, "s1 g3", MX + 9.4, 3.75, W - 9.4, 0.95, "A short cycle list, with reasons", { fill: C.slate, pt: 16 });
    bullets(s, "s1 bullets", [
      "A committee cannot visit everything every cycle: whom to visit first? These are the chairman's statements, not our measurement.",
      "The gap: ACUD's data (plot boundaries, handover dates, supervisor reports, field review records) is what would turn our public-data screening into operation.",
    ], MX, 4.9, W, 1.5, 16);
  },
});

// 2
slides.push({
  title: "The question and the decision", time: "0:15",
  md: [
    "- Question: which R7 compounds should the committee visit first next cycle, and why?",
    "- The observatory ranks; the committee decides.",
    "- Scope: R7 only, 12 coded compounds, reporting quarter 2026Q3, cycle capacity 4.",
    "- As-is → to-be: today every one of the 12 compounds gets a field review every 3 months (4 visits a year each); tomorrow a cycle list of at most 4 compounds from levels 1-3, each with a reason sentence, and the committee decides.",
    "- ACUD has not given us visit times or missed cases, so the as-is pain is not measured.",
    "- Wording rule: the list says \"no building activity since X\" or \"passed its first date by Y\", never a label on a developer.",
    "- Visual: as-is → to-be flow of two boxes and a 12 → 4 funnel (12 R7 compounds → 4 visits per cycle).",
  ],
  source: ["`configs/cost_assumptions.yaml` (`projects: 12`, `visits_per_year: 4`), `docs/requirements/01-specs.md` (sections 2, 7 and 12)."],
  note: "Speaker note: 0:15 · criteria 1, 2, 3. The question and the scope; the new process follows on slide 2b and the decision on slide 11.",
  build(s) {
    const bw = 5.5;
    box(s, "s2 asis", MX, TOP + 0.1, bw, 1.3, "Today (as-is): every one of the 12 compounds gets a field review every 3 months, 4 visits a year each.", { fill: C.slate, pt: 16 });
    arrow(s, MX + bw + 0.3, TOP + 0.55, 0.5, 0.5);
    box(s, "s2 tobe", MX + bw + 1.1, TOP + 0.1, bw + 0.03, 1.3, "Tomorrow (to-be): a cycle list of at most 4 compounds from levels 1-3, each with a reason sentence. The committee decides.", { fill: C.red, pt: 16 });
    const fw = 7.0;
    box(s, "s2 f12", MX, 2.95, fw, 0.5, "12 R7 compounds in scope", { fill: C.slate, pt: 16 });
    box(s, "s2 f4", MX, 3.5, (fw * 4) / 12, 0.5, "4 visits per cycle", { fill: C.red, pt: 14 });
    s.addText("Capacity 4 of 12 compounds, from levels 1-3", { x: MX + (fw * 4) / 12 + 0.15, y: 3.5, w: 6, h: 0.5, fontFace: BODY, fontSize: 14, color: C.ink, align: "left", valign: "middle", margin: 0 });
    bullets(s, "s2 bullets", [
      "Question: which R7 compounds should the committee visit first next cycle, and why?",
      "The observatory ranks; the committee decides.",
      "Scope: R7 only, 12 coded compounds, reporting quarter 2026Q3, cycle capacity 4.",
      "ACUD has not given us visit times or missed cases, so the as-is pain is not measured.",
      "Wording rule: the list says \"no building activity since X\" or \"passed its first date by Y\", never a label on a developer.",
    ], MX, 4.25, W, 2.15, 16);
  },
});


// 2b: to-be flow (docs/deliverables/to-be.md, "The new process")
function link(slide, x1, y1, x2, y2) {
  slide.addShape(pres.ShapeType.line, {
    x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.max(Math.abs(x2 - x1), 0.001), h: Math.max(Math.abs(y2 - y1), 0.001),
    flipH: x2 < x1, flipV: y2 < y1, line: { color: C.ink, width: 1.5, endArrowType: "triangle" },
  });
}
function edgeLabel(slide, text, x, y, w, align = "left") {
  slide.addText(text, { x, y, w, h: 0.4, fontFace: BODY, fontSize: 11, italic: true, color: C.ink, align, valign: "middle", margin: 0 });
}
slides.push({
  title: "To-be: the new process", time: "0:30",
  md: [
    "- New process (proposed): public satellite data every quarter and published developer statements → pipeline and quality gates → priority list (levels 1-4 with a written reason, capacity 4) → the committee decides → field visit, or watch next quarter → the result is recorded on the Compound file screen in the visit log → the visit log counts false alarms and misses and feeds the next run.",
    "- The system recommends; the committee decides.",
    "- Roles: the Track A owner runs the pipeline and the quality gates every quarter, reviewed by a second team member; the committee decides which compounds to visit; the field visit lead records the result (progressing, stalled, complete, not done); the ACUD data custodian keeps the code-to-name mapping.",
    "- Proposed targets: every compound at level 1 or 2 visited within the quarter (capacity 4 covered all of them in 31 of 31 quarters, 2019Q1-2026Q3); 12 of 12 visit results recorded in the pilot quarter.",
    "- Status: proposed by the team, not approved by ACUD.",
    "- Visual: flowchart of the new process (from `docs/deliverables/to-be.md`).",
  ],
  source: ["`docs/deliverables/to-be.md` (the new process, roles and proposed targets)."],
  note: "Speaker note: 0:30 · criteria 3, 5. Walk the loop once from satellite data to the visit log; stress that the committee decides and every visit result comes back as ground truth. Targets are proposals, not approved by ACUD.",
  build(s) {
    const y0 = 2.15, bh = 0.75, cy = y0 + bh / 2;
    box(s, "s2b S", MX, 1.5, 2.5, bh, "Public satellite data, every quarter", { fill: C.slate });
    box(s, "s2b T", MX, 2.8, 2.5, bh, "Published developer statements", { fill: C.slate });
    box(s, "s2b P", 3.7, y0, 2.3, bh, "Pipeline and quality gates", { fill: C.slate });
    box(s, "s2b L", 6.7, y0, 2.3, bh, "Priority list, capacity 4", { fill: C.slate });
    s.addShape(pres.ShapeType.diamond, { x: 9.55, y: 1.85, w: 2.4, h: 1.35, fill: { color: C.red }, line: { color: C.red } });
    s.addText("Committee decides", { x: 9.85, y: 1.85, w: 1.8, h: 1.35, fontFace: BODY, fontSize: 14, bold: true, color: C.white, align: "center", valign: "middle", margin: 0 });
    box(s, "s2b F", 8.1, 4.0, 2.1, 0.7, "Field visit", { fill: C.slate });
    box(s, "s2b W", 10.45, 4.0, 2.28, 0.7, "Watch next quarter", { fill: C.slate });
    box(s, "s2b R", 3.7, 4.0, 2.3, 0.7, "Visit log", { fill: C.red });
    link(s, MX + 2.5, 1.5 + bh / 2, 3.7, cy - 0.12);
    link(s, MX + 2.5, 2.8 + bh / 2, 3.7, cy + 0.12);
    link(s, 6.0, cy, 6.7, cy);
    edgeLabel(s, "levels 1-4 with a written reason", 5.2, 1.75, 2.3, "center");
    link(s, 9.0, cy, 9.55, cy);
    link(s, 10.4, 3.2, 9.15, 4.0);
    edgeLabel(s, "visit", 9.0, 3.3, 0.8, "right");
    link(s, 11.1, 3.2, 11.6, 4.0);
    edgeLabel(s, "no visit", 11.45, 3.3, 1.2);
    link(s, 8.1, 4.35, 6.0, 4.35);
    edgeLabel(s, "result recorded on the Compound file screen", 6.0, 3.5, 2.6);
    link(s, 4.85, 4.0, 4.85, y0 + bh);
    edgeLabel(s, "counts false alarms and misses", 4.95, 3.0, 1.9);
    bullets(s, "s2b bullets", [
      "Roles: the Track A owner runs the pipeline and gates each quarter (second reviewer); the committee decides; the field visit lead records progressing, stalled, complete or not done; the ACUD data custodian keeps the code-to-name mapping.",
      "Proposed targets: every level 1 or 2 compound visited within the quarter (capacity 4 covered all of them in 31 of 31 quarters); 12 of 12 visit results recorded in the pilot quarter.",
      "Status: proposed by the team, not approved by ACUD. The system recommends; the committee decides.",
    ], MX, 4.95, W, 1.55, 14);
  },
});

// 3
slides.push({
  title: "Data", time: "0:30",
  md: [
    "- 1,009 of 1,026 documented facts passed independent review. This is the figure stated in the spec, not a recount.",
    "- Origin key on every number: 🟢 real, 🔵 derived, 🟠 generated.",
    "- Real: satellite series, statements, laws. Generated: finance, supervisor reports, meters, complaints (only ACUD holds the real ones).",
    "- Pipeline: public sources → prepared v7 release (84 frozen inputs in data/REBUILD_INPUTS.csv) → dashboard.",
    "- Public and derived tables: 12 compounds, 516 compound-quarters (2016Q1-2026Q3), 57 statements, 372 KPI rows (cutoffs 2019Q1-2026Q3).",
    "- Visual: stat callout (1,009 of 1,026), origin-key table and a three-step pipeline graphic.",
  ],
  source: ["`docs/requirements/01-specs.md` (section 12); `data/DATASET_CONTRACT.md` (tables and sizes); `data/REBUILD_INPUTS.csv` (84 inputs)."],
  note: "Speaker note: 0:30 · criteria 2, 8. Point to the origin key; it is used on every later slide. The installed data has no facts register, so 1,009 of 1,026 is the figure stated in the spec (section 12), not a recount; the dashboard's data-trust screen shows the same documented figure.",
  build(s) {
    stat(s, "s3 stat", MX, TOP + 0.1, 3.9, 2.2, "1,009 of 1,026", "documented facts passed independent review");
    table(s, "s3 table", [
      ["Origin", "Contents"],
      ["🟢 Real", "Satellite series, statements, laws"],
      ["🔵 Derived", "Computed from the real inputs"],
      ["🟠 Generated", "Finance, supervisor reports, meters, complaints (only ACUD holds the real ones)"],
    ], MX + 4.2, TOP + 0.1, W - 4.2, [2.0, W - 4.2 - 2.0], 14, 0.55);
    const pw = (W - 2 * 0.5) / 3;
    ["Public sources and statements (🟢 real)", "Prepared v7 release: 84 frozen inputs (data/REBUILD_INPUTS.csv)", "Dashboard: Track A real or derived; Track B marked 🟠"].forEach((tx, i) => {
      box(s, "s3 pipe " + i, MX + i * (pw + 0.5), 3.85, pw, 0.85, tx, { fill: i === 2 ? C.red : C.slate, pt: 14 });
      if (i < 2) arrow(s, MX + i * (pw + 0.5) + pw + 0.05, 4.07, 0.4, 0.4);
    });
    bullets(s, "s3 bullets", [
      "The figure is the one stated in the spec, not a recount. The origin key (🟢 🔵 🟠) is on every later number.",
      "Public and derived tables: 12 compounds, 516 compound-quarters (2016Q1-2026Q3), 57 statements, 372 KPI rows.",
    ], MX, 4.9, W, 1.5, 16);
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
    "- Visual: three-row source table (source · gives · role), with the compound file screen.",
    ...shotMd(["file"]),
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
    ], MX, 4.15, W - 3.7, 2.25, 16);
    shot(s, "file", MX + W - 3.4, 4.1, 3.4);
  },
});

// 5
slides.push({
  title: "The Track A rule", time: "0:45",
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
  note: "Speaker note: 0:45 · criteria 3, 4. The worst signal sets the level, without weights, and each level maps to an action.",
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
  title: "Live demo (Track A)", time: "1:00",
  md: [
    "- Priority map, cycle list (capacity 4, levels 1-3), open one compound, read its reason sentence, open the inspection file, record a visit result.",
    "- Everything on screen in Track A is real or derived. No generated number appears on the map.",
    "- Dependency: the demo needs the dashboard to run from stored files. Run command: `make run (team_run --full, which calls run_all)`, the one run command per board task T-AH-19.",
    "- Visual: five-step flow (priority map → cycle list → reason sentence → inspection file → visit result), with two dashboard screenshots.",
    ...shotMd(["top", "mapPanel"]),
  ],
  source: ["`docs/deliverables/user-guide.md`; board task T-AH-19 in `docs/requirements/02-team-roles-and-tasks.md`."],
  note: "Speaker note: 1:00 · criterion 4. Follow the alert to the action: level, cycle list, inspection file, visit form.",
  build(s) {
    const steps = ["Priority map", "Cycle list (capacity 4, levels 1-3)", "Compound reason sentence", "Inspection file", "Visit result recorded"];
    const bw = 1.95, gap = (W - 5 * bw) / 4;
    steps.forEach((t, i) => {
      box(s, "s6 step " + i, MX + i * (bw + gap), TOP, bw, 0.9, t, { fill: i === 4 ? C.red : C.navy, pt: 14 });
      if (i < 4) arrow(s, MX + i * (bw + gap) + bw + (gap - 0.3) / 2, TOP + 0.25, 0.3, 0.4);
    });
    const iw = (W - 0.2) / 2;
    shot(s, "top", MX, 2.3, iw);
    shot(s, "mapPanel", MX + iw + 0.2, 2.3, iw);
    bullets(s, "s6 bullets", [
      "Track A on screen is real or derived, no generated number on the map. Run: make run (T-AH-19), from stored files.",
    ], MX, 6.08, W, 0.45, 14);
  },
});

// 6b
slides.push({
  title: "Search, filters and map click", time: "0:45",
  md: [
    "- One search box takes a compound code (C..) or a developer code (D..); a prefix works. Typing \"C1\" narrows the map to 6 of 12 compounds, and the level legend shows the counts.",
    "- Filters: as-of quarter, priority level, developer code, minimum K2 / K3 / K6 and \"Cycle list only\". The caption says how many compounds are shown, and unknown K values stay only while their minimum is 0.",
    "- The rank stays the quarter's visit order while you filter.",
    "- Click a block on the map: the sidebar opens the \"Selected compound\" panel with its stored values and drill-downs (\"Open compound file\" button). \"Clear selection\" resets it.",
    "- Codes only, no names.",
    "- Visual: two dashboard screenshots (search \"C1\"; map click and sidebar panel).",
    ...shotMd(["search", "mapPanel"]),
  ],
  source: ["`app.py` (`render_filters`, `open_clicked_compound`, `render_selected_compound_panel`), `src/dashboard/insights.py` (`filter_compounds`); board tasks T-NA-11, T-NA-12, T-NA-13 and T-EL-21 in `docs/requirements/02-team-roles-and-tasks.md`."],
  note: "Speaker note: 0:45 · criterion 4. Live: type C1 in the search, set a priority level filter, click a block on the map, show the sidebar panel, then Clear selection.",
  build(s) {
    const iw = 3.9;
    shot(s, "search", MX, TOP, iw);
    shot(s, "mapPanel", MX + iw + 0.2, TOP, iw);
    bullets(s, "s6b bullets", [
      "One search box: a compound code (C..) or developer code (D..); a prefix works. \"C1\" shows 6 of 12 compounds.",
      "Filters: as-of quarter, priority level, developer, minimum K2 / K3 / K6, cycle list only.",
      "Rank stays the quarter's visit order when you filter.",
      "Click a block on the map: the sidebar shows that compound. \"Clear selection\" resets. Codes only.",
    ], MX + 2 * iw + 0.4, TOP, W - 2 * iw - 0.4, 4.9, 14);
  },
});

// 6c
slides.push({
  title: "Four screens, one path from alert to action", time: "0:15",
  md: [
    "- 1 Priority map: whom should the committee visit first?",
    "- 2 Compound file: why this one? Evidence behind the priority level.",
    "- 3 District view: what does the system give the committee, and when does it fail?",
    "- 4 Digital twin what if: who would change if costs, collections or visit capacity changed? (Track B, generated)",
    "- Alert → action: level → cycle list → compound file → visit form → recorded visit.",
    "- Audience test: what the teammate reviews changed is logged; the ten-second test with a committee member is still to be run.",
    "- Visual: four screen cards (screen 4 marked generated) and an alert-to-action arrow row.",
  ],
  source: ["`docs/deliverables/user-guide.md` (screen subtitles), `docs/deliverables/audience-test.md`, `docs/deliverables/display-rules-check.md`."],
  note: "Speaker note: 0:15 · criterion 4. Name who uses each screen, follow the alert to the action, and say the committee-member test is still to be run.",
  build(s) {
    const cards = [["1 · Priority map", "Whom first?"], ["2 · Compound file", "Why this one?"], ["3 · District view", "What does the system give, and when does it fail?"], ["4 · Digital twin what if", "Who changes if costs, collections or capacity change? Track B, generated"]];
    const cw = (W - 3 * 0.15) / 4;
    cards.forEach(([a, b], i) => {
      const x = MX + i * (cw + 0.15), gen = i === 3;
      s.addShape(pres.ShapeType.rect, { x, y: TOP, w: cw, h: 1.7, fill: { color: gen ? C.orange : C.card }, line: { color: gen ? C.orange : C.card } });
      s.addShape(pres.ShapeType.rect, { x, y: TOP, w: cw, h: 0.08, fill: { color: gen ? C.navy : C.red }, line: { color: gen ? C.navy : C.red } });
      check("s6c card " + i, [a, b], 14, cw - 0.3, 1.5);
      s.addText([
        { text: a, options: { bold: true, fontFace: HEAD, fontSize: 16, breakLine: true } },
        { text: b, options: { fontFace: BODY, fontSize: 14 } },
      ].map((r) => ({ text: r.text, options: { color: gen ? C.white : C.ink, paraSpaceAfter: 4, ...r.options } })), { x: x + 0.15, y: TOP + 0.18, w: cw - 0.3, h: 1.45, align: "left", valign: "top", margin: 0 });
    });
    const steps = ["Level", "Cycle list", "Compound file", "Visit form", "Recorded visit"];
    const bw = 1.95, gap = (W - 5 * bw) / 4;
    steps.forEach((t, i) => {
      box(s, "s6c step " + i, MX + i * (bw + gap), 3.5, bw, 0.8, t, { fill: i === 4 ? C.red : C.navy, pt: 14 });
      if (i < 4) arrow(s, MX + i * (bw + gap) + bw + (gap - 0.3) / 2, 3.75, 0.3, 0.4);
    });
    bullets(s, "s6c bullets", [
      "Alert to action: the level sets the cycle list, the compound file gives the reason, the visit form records the result.",
      "Audience test: the teammate reviews changed the screens (audience-test.md). The ten-second test with a committee member is still to be run.",
    ], MX, 4.6, W, 1.8, 16);
  },
});

// 7
slides.push({
  title: "Backtest: 1 of 6 and why", time: "1:00",
  md: [
    "- Six public R7 cases, checked with the clock frozen. Codes only, even on this slide.",
    "- Early alert in 1 of 6 cases (after-start reading, case C21) and 0 of 6 (point-in-time reading).",
    "- The target of 5 cases was fixed before computing, was not lowered and was not met.",
    "- Imaging was sufficient in every case (at least 10 images per quarter). In the five missed cases the sites were seen as active, so the rule had no stall to detect. The rule measures stalls and passed dates, not pace against plan.",
    "- The one hit (C21) came from a start date set by publication timing and a lag in the activity score, not from a real stall during construction, so it does not carry over to the other five.",
    "- These counts do not prove why each delay happened.",
    "- Visual: three stat callouts (1 of 6 · 0 of 6 · 5 required, not achieved), with the C21 district view.",
    ...shotMd(["district"]),
  ],
  source: ["`data/BACKTEST_CURRENT.md`, `data/experiments/35_backtest_diagnosis/DIAGNOSIS.md`."],
  note: "Speaker note: 1:00 · criterion 6. Lead with the miss, and say the target was fixed before computing.",
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
    ], MX, 3.15, 7.2, 3.25, 16);
    shot(s, "district", MX + 7.4, 3.15, W - 7.4);
  },
});

// 8
const RECALL = [["Public rule", 3], ["Combined rule", 3], ["Logistic, satellite", 1], ["Logistic, combined", 2], ["Boosting, satellite", 4], ["Boosting, combined", 1]];
slides.push({
  title: "Track B: generated data", time: "0:45",
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
  note: "Speaker note: 0:45 · criterion 6. Generated data only; with 4 test cases the methods cannot be separated. For questions, complaints classifier: the keyword baseline scored 0.27 accuracy on the 104-row benchmark and 0.37 on the 30-item check set; TF-IDF plus logistic scored 0.22 and 0.30, respectively. Accuracy on texts written by the team does not prove accuracy on real complaints.",
  build(s) {
    banner(s);
    bullets(s, "s8 bullets", [
      "Target: distressed / not_distressed in the next six months. Completion prediction is out of scope.",
      "96 training rows, 48 test rows; only 4 test rows are distressed, so power is very low.",
      "Boosting 4 of 4 rests partly on height; without height (v2a) it is 1 of 4.",
      "Random top-4 baseline: mean 0.335, 95% interval 0.000 to 0.750 (2,000 draws).",
      "With 4 cases the methods cannot be separated, and combining ACUD-style data did not clearly help. Scores are diagnostic, not real-world accuracy.",
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
    "- Visual: scenario table (S1 · S2 · S3 and rows changed) and the scenario panel of the dashboard (cropped).",
    ...shotMd(["twin"]),
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
    ], MX, 1.95, W, [1.6, 4.0, W - 5.6], 14, 0.5, C.orange);
    shot(s, "twin", MX, 4.3, 6.6);
    bullets(s, "s8b bullets", [
      "Light compound-level observatory: observed state from satellites and statements, simulated hidden state from the generator.",
      "Demo S3 live. Say plainly that S1 and S2 change nothing in the list or levels.",
      "Orange banner on screen, no map. Not a 3D or real-time observatory.",
    ], MX + 6.85, 4.3, W - 6.85, 2.1, 14);
  },
});

// 8c
slides.push({
  title: "Ask the project: the chatbot", time: "0:45",
  md: [
    "- Flow: question → intent router (10 intents: greeting, out_of_scope, complaints, inspection_visits, inspection_priority, knowledge, rules, published_statements, project_info, project_overview) → hybrid retrieval (DuckDB facts from the v7 release + Chroma vector search over statements, complaints and knowledge documents) → answer → sources shown.",
    "- Answer: the Gemini model set in `configs/ai.yaml` when model calls are approved and within the call budget, otherwise a local answer.",
    "- Opens from the dashboard's 💬 button (port 8001).",
    "- Follow-up questions keep the last compound code of the conversation.",
    "- Generated items stay labelled: the complaints and visit records are synthetic.",
    "- Visual: native flow of five steps and a chatbot answer screenshot.",
    ...shotMd(["chatbot"]),
  ],
  source: ["`chatbot/app/retrieval/router.py` (intents), `chatbot/app/retrieval/hybrid.py`, `chatbot/app/api/main.py` (session context), `chatbot/app/generation/gemini_client.py`, `configs/ai.yaml`, `README.md`."],
  note: "Speaker note: 0:45 · criterion 4. Live: open the 💬 button, ask one question, show the cited sources; say generated items stay labelled.",
  build(s) {
    const steps = ["Question", "Intent router (10 intents)", "Hybrid retrieval: DuckDB facts + Chroma search", "Answer: Gemini if approved and within budget, else local", "Sources shown"];
    const bw = 2.1, gap = (W - 5 * bw) / 4;
    steps.forEach((t, i) => {
      box(s, "s8c step " + i, MX + i * (bw + gap), TOP, bw, 1.35, t, { fill: i === 4 ? C.red : C.navy, pt: 14 });
      if (i < 4) arrow(s, MX + i * (bw + gap) + bw + (gap - 0.3) / 2, TOP + 0.45, 0.3, 0.4);
    });
    bullets(s, "s8c bullets", [
      "Opens from the dashboard's 💬 button (port 8001).",
      "Follow-up questions keep the last compound code.",
      "Generated items stay labelled: complaints and visit records are synthetic.",
      "Retrieval reads the v7 release facts and the statements, complaints and knowledge documents.",
    ], MX, 3.0, 6.9, 3.4, 14);
    shot(s, "chatbot", MX + W - 4.9, 3.0, 4.9);
  },
});

// 8d
slides.push({
  title: "What the chatbot knows, and its limits", time: "0:45",
  md: [
    "- Knowledge: 9 sourced documents (ACUD site, Decree 2184/2022, Building Law 119/2008 art. 54, Law 151/2020, Dynamic World, Open Buildings, Esri Wayback, ISO 37120/37122, team SLA note) plus the project's data.",
    "- Evaluation: 8 of 8 intent tests passed (2026-11-03) and 5 of 5 retrieval checks passed. These are the team's own small tests, not an accuracy claim.",
    "- Governance: model calls only with approval in `configs/ai.yaml` (`chatbot.approval: approved`, `max_calls_total: 200`, approved by the project owner on 2026-11-04), then local answers.",
    "- Codes only. Not legal advice.",
    "- Visual: two stat callouts (8 of 8 · 5 of 5) and a call-budget box (200 calls).",
  ],
  source: ["`chatbot/knowledge/SOURCES.csv`, `chatbot/evaluation_results.json`, `chatbot/retrieval_evaluation_results.json`, `configs/ai.yaml`."],
  note: "Speaker note: 0:45 · criteria 8, 9. Say the tests are the team's own and small; model calls need the owner's approval and stop at 200, then local answers. Codes only, not legal advice.",
  build(s) {
    const w = 3.6;
    stat(s, "s8d a", MX, TOP + 0.05, w, 1.7, "8 of 8", "intent tests passed (2026-11-03)");
    stat(s, "s8d b", MX + w + 0.2, TOP + 0.05, w, 1.7, "5 of 5", "retrieval checks passed");
    box(s, "s8d budget", MX + 2 * (w + 0.2), TOP + 0.05, W - 2 * (w + 0.2), 1.7, "Call budget: 200 model calls in total (approved by the project owner on 2026-11-04), then local answers", { fill: C.red, pt: 16 });
    bullets(s, "s8d bullets", [
      "Knowledge: 9 sourced documents (ACUD site, Decree 2184/2022, Building Law 119/2008 art. 54, Law 151/2020, Dynamic World, Open Buildings, Esri Wayback, ISO 37120/37122, team SLA note) plus the project's data.",
      "The tests are the team's own and small. They are not an accuracy claim.",
      "Model calls only with approval in configs/ai.yaml (chatbot.approval: approved), then local answers.",
      "Codes only. Not legal advice.",
    ], MX, 3.4, W, 3.0, 16);
  },
});

// 9
slides.push({
  title: "Value in EGP (3 settings)", time: "1:00",
  md: [
    "- Visiting 4 compounds per cycle instead of all 12: 16 visits a year instead of visiting every compound each cycle.",
    "- Under these assumptions, from 0.007 to 0.102 million EGP per year.",
    "- Cost inputs are public proxies or assumptions. Even the conservative setting is positive, but small.",
    "- Cost per visit (2,000 / 3,000 / 4,000 EGP) is an assumption based on a team of 3 at published engineer pay plus assumed transport. Operating cost and missed cases are public proxies (CBE, Hetzner, WageIndicator, chairman's 7-8% statement); the cost of a late case is a placeholder.",
    "- The cost of a false alarm against the cost of a missed case has not been measured.",
    "- Not a measured saving.",
    "- Visual: two stat callouts (0.007 and 0.102 million EGP per year) and a three-setting table (cost per visit, operating cost, missed cases per year).",
  ],
  source: ["`configs/cost_assumptions.yaml` (the same file holds the three settings, the proxy values and the placeholder); `docs/deliverables/01-presentation/rubric-map.md` (criterion 6 gap)."],
  note: "Speaker note: 1:00 · criterion 7. Compare with the current policy of visiting all 12; say the conservative setting is positive but small. The cost of a late case is a placeholder of 20,000 EGP per missed case in all three settings.",
  build(s) {
    stat(s, "s9 lo", MX, TOP + 0.05, 3.0, 1.9, "0.007", "million EGP per year, low end");
    stat(s, "s9 hi", MX + 3.2, TOP + 0.05, 3.0, 1.9, "0.102", "million EGP per year, high end");
    table(s, "s9 table", [
      ["Setting", "Cost per visit (EGP)", "Operating cost (EGP/yr, proxy)", "Missed cases per year (proxy)"],
      ["Conservative", "2,000", "16,800", "2"],
      ["Central", "3,000", "9,700", "1"],
      ["Optimistic", "4,000", "6,000", "1"],
    ], MX + 6.6, TOP + 0.05, W - 6.6, [1.35, 1.2, 1.5, W - 6.6 - 4.05], 12, 0.5);
    bullets(s, "s9 bullets", [
      "Visiting 4 compounds per cycle instead of all 12: 16 visits a year.",
      "Cost inputs are public proxies or assumptions; the conservative setting is positive but small. Not a measured saving.",
      "Cost per visit (assumption): a team of 3 at published engineer pay plus assumed transport. Operating cost and missed cases are public proxies; the cost of a late case is a placeholder.",
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
  ["Complaint text", "Masking does not prove every real name is removed; real text needs further review. The chatbot sees only generated complaints."],
  ["Law 151/2020", "Interpretation needs the data custodian's review. Not legal advice."],
  ["Handover", "Guides, method card and checklist are in the repo; no one outside the team has rebuilt the system from them yet."],
];
slides.push({
  title: "Risks and responsible use", time: "0:45",
  md: [
    ...RISKS.map(([a, b]) => `- ${a}: ${b}`),
    "- The committee decides; every visit result is recorded to build real ground truth.",
    "- Knowledge transfer: technical operations guide, committee user guide, handover pack, method card and final checklist are in the repo; the user guide was checked against the code, not in a browser.",
    "- Visual: eight cards (seven risks and the committee-decides control).",
  ],
  source: ["`docs/deliverables/responsible-ai.md`, `docs/requirements/01-specs.md` (Law 151/2020).", "(knowledge transfer) `docs/deliverables/technical-track-a.md`, `docs/deliverables/user-guide.md`, `docs/deliverables/knowledge-transfer.md`, `docs/deliverables/method-card.md`, `docs/deliverables/final-checklist.md`."],
  note: "Speaker note: 0:45 · criteria 8, 9. A level sets the visit order and finds nothing against anyone. Then give one line on the handover documents. The committee decides, and every visit result is recorded to build real ground truth. The user guide was checked against the code, not in a browser.",
  build(s) {
    const cards = [...RISKS, ["The committee decides", "Every visit result is recorded to build real ground truth."]];
    const cw = (W - 3 * 0.15) / 4, ch = 2.35;
    cards.forEach(([a, b], i) => {
      const x = MX + (i % 4) * (cw + 0.15), y = TOP + Math.floor(i / 4) * (ch + 0.12), last = i === cards.length - 1;
      s.addShape(pres.ShapeType.rect, { x, y, w: cw, h: ch, fill: { color: last ? C.red : C.card }, line: { color: last ? C.red : C.card } });
      s.addShape(pres.ShapeType.rect, { x, y, w: cw, h: 0.08, fill: { color: last ? C.navy : C.red }, line: { color: last ? C.navy : C.red } });
      check("s10 card " + i, [a, b], 14, cw - 0.3, ch - 0.2);
      s.addText([
        { text: a, options: { bold: true, fontFace: HEAD, fontSize: 16, breakLine: true } },
        { text: b, options: { fontFace: BODY, fontSize: 14 } },
      ].map((r) => ({ text: r.text, options: { color: last ? C.white : C.ink, paraSpaceAfter: 4, ...r.options } })), { x: x + 0.15, y: y + 0.18, w: cw - 0.3, h: ch - 0.26, align: "left", valign: "top", margin: 0 });
    });
  },
});

// 10b
slides.push({
  title: "Launching in production", time: "0:30",
  md: [
    "- What runs: the Streamlit dashboard (`uv run --locked streamlit run app.py`), the quarterly data run (`uv run --locked --offline python -m src.pipeline.team_run`) and prepared data v7 (`releases/ready-data`).",
    "- Where (proposed, not deployed): a server or VM managed by ACUD, inside ACUD's network, to be agreed with ACUD. Data stays with ACUD; exports use codes only; private mappings never leave the data custodian.",
    "- Controls: thresholds and capacity change only by reviewed decision; chatbot model calls only with owner approval and within the approved budget of 200 calls (`configs/ai.yaml`), then local answers; every visit result is recorded in ops_visits.",
    "- Monitoring: the quarterly procedure and its quality gates; any STOP keeps outputs for diagnosis, writes no manifest and blocks packaging.",
    "- Rollback: switch the activity source to K1 (a recorded decision) and keep prior releases available, as slide 11 says.",
    "- Quarterly cycle: quarter data refresh → gates (STOP/FIX/FLAG) → cycle list → visits → recorded results → next quarter. A FLAG needs a recorded review decision; a STOP blocks delivery. If source coverage fails, affected observations are marked not assessable; an automatic K1 switch is not yet established.",
    "- Visual: four-step flow (prepare data → run rule → publish dashboard → committee visits and records), a six-step quarterly cycle and a STOP / rollback box.",
  ],
  source: ["`README.md`, `CLAUDE.md`, `docs/deliverables/technical-track-a.md` (quarterly monitoring procedure, STOP, K1 switch; states no deployment is implied), `docs/deliverables/data-request.md`, `docs/deliverables/responsible-ai.md`, `docs/deliverables/governance-cards.md`, `configs/ai.yaml`, `src/dashboard/ops_visits.py`."],
  note: "Speaker note: 0:30 · criteria 5, 9. Technical launch only; phases are on the next slide. Hosting is a proposal to agree with ACUD, not a deployed system. Any STOP writes no manifest; the fallback is K1 and the prior release.",
  build(s) {
    const steps = ["Prepare data (v7, codes only)", "Run rule (quarterly team_run)", "Publish dashboard (Streamlit)", "Committee visits and records (ops_visits)"];
    const bw = 2.6, gap = (W - 4 * bw) / 3;
    steps.forEach((t, i) => {
      box(s, "s10b step " + i, MX + i * (bw + gap), TOP + 0.05, bw, 1.0, t, { fill: i === 3 ? C.red : C.navy, pt: 14 });
      if (i < 3) arrow(s, MX + i * (bw + gap) + bw + (gap - 0.3) / 2, TOP + 0.35, 0.3, 0.4);
    });
    const cyc = ["Quarter data refresh", "Gates (STOP / FIX / FLAG)", "Cycle list", "Visits", "Results recorded", "Next quarter"];
    const cw = (W - 5 * 0.3) / 6;
    cyc.forEach((tx, k) => {
      box(s, "s10b cyc " + k, MX + k * (cw + 0.3), 2.65, cw, 0.8, tx, { fill: k === 1 ? C.red : C.slate, pt: 14 });
      if (k < 5) arrow(s, MX + k * (cw + 0.3) + cw + 0.02, 2.9, 0.26, 0.3);
    });
    bullets(s, "s10b bullets", [
      "Runs: Streamlit dashboard, quarterly team_run, prepared data v7 (releases/ready-data).",
      "Where (proposed, not deployed): ACUD-managed server or VM inside ACUD's network. Data stays with ACUD; codes only.",
      "Controls: thresholds and capacity change only by reviewed decision; chatbot model calls only within the approved 200-call budget; every visit result recorded.",
    ], MX, 3.65, 7.4, 2.75, 14);
    box(s, "s10b stop", MX + 7.65, 3.65, W - 7.65, 2.7, "STOP and rollback: a STOP keeps outputs for diagnosis, writes no manifest and blocks packaging. If source coverage fails, mark affected observations not assessable and review. Fallback: K1 (a recorded decision) with prior releases kept; an automatic switch is not yet established.", { fill: C.red, pt: 14 });
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
  if (sp.cover) s.background = { color: C.white };
  else base(s, sp.title, sp.source, !!sp.dark);
  sp.build(s);
  s.addNotes(sp.note);
});

// ---------- markdown ----------
const labels = ["0", "1", "2", "2b", "3", "4", "5", "6", "6b", "6c", "7", "8", "8b", "8c", "8d", "9", "10", "10b", "11"];
const md = [
  "# Presentation: 19 slides (title slide 0, then 1-11 with 2b after 2, 6b and 6c after 6, 8b, 8c and 8d after 8, and 10b after 10)",
  "",
  "Tasks T-SA-06 and T-EL-25. Draft text for review. This file holds the on-slide content and speaker notes of `presentation.pptx`, slide for slide in the same order. Length: 12 min, the limit set by criterion 10 of the instructor rubric (`docs/requirements/ACUD-Rubric.md`); the time budget and the criteria each slide answers follow `docs/deliverables/01-presentation/rubric-map.md` (presentation plan) and are stated in each speaker note (total 12:00). Numbers come only from repo files and carry an origin mark: 🟢 real · 🔵 derived · 🟠 generated (\"Synthetic - for training only\"). Compounds and developers appear as codes only; the only names are the supervisor and team on the title slide. The words \"risk level\", \"distressed\" (for a real compound) and any completion % are not used. Some caveats are in the speaker notes.",
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

// ---------- html (same spec; colors from palette.md; no external scripts or fonts) ----------
const esc = (t) => t.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
const inline = (t) => esc(t).replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>").replace(/`([^`]+)`/g, "<code>$1</code>");
const SYN_TEXT = "Synthetic - for training only";
function htmlList(lines) {
  // md lines: "- x" top level, "  - x" nested under the previous item.
  let out = "<ul>", open = false;
  lines.forEach((l) => {
    const nested = l.startsWith("  - ");
    const t = l.replace(/^\s*- /, "");
    if (nested) { if (!open) { out += "<ul>"; open = true; } out += `<li dir="auto">${inline(t)}</li>`; return; }
    if (open) { out += "</ul></li>"; open = false; } else if (out.endsWith("</li>") === false && out !== "<ul>") out += "";
    out += `<li dir="auto">${inline(t)}`;
    out += "</li>";
  });
  return out + (open ? "</ul></li>" : "") + "</ul>";
}
const sections = slides.map((sp, i) => {
  const id = `slide-${labels[i]}`;
  if (sp.cover) {
    const [name, slogan, ...rest] = sp.md.map((l) => l.replace(/^- /, ""));
    return `<section id="${id}" class="cover" aria-label="Slide ${labels[i]}">\n<p class="logos"><img src="../02-video/logo-ACUD.png" alt="ACUD" height="48"> <img src="../02-video/logo-digilians.png" alt="Digilians" height="62"></p>\n<h1 dir="auto">${inline(name)}</h1>\n<p class="slogan" dir="auto">${inline(slogan)}</p>\n${rest.map((r) => `<p dir="auto">${inline(r)}</p>`).join("\n")}\n<p class="note" dir="auto">${inline(sp.note)}</p>\n</section>`;
  }
  const lines = sp.md.filter((l) => !l.includes(SYN_TEXT) && !l.startsWith("- Screenshot: "));
  const figs = sp.md.filter((l) => l.startsWith("- Screenshot: ")).map((l) => {
    const [, file, cap] = l.match(/`assets\/([^`]+)`, "([^"]+)"/);
    const c = Object.values(SHOTS).find((v) => v.file === file).crop;
    const st = c ? ` style="width:${((1600 / c.w) * 100).toFixed(2)}%;margin-left:-${((c.x / c.w) * 100).toFixed(2)}%;margin-top:-${((c.y / c.w) * 100).toFixed(2)}%"` : "";
    const img = `<img src="assets/${file}" alt="${esc(cap)}"${st}>`;
    return `<figure>${c ? `<div class="cropbox" style="--ar:${c.w}/${c.h}">${img}</div>` : img}<figcaption>${esc(cap)}</figcaption></figure>`;
  }).join("\n");
  const banner = sp.md.some((l) => l.includes(SYN_TEXT)) ? `<p class="banner">${esc(SYN)}</p>\n` : "";
  const srcs = sp.source.map((src) => `<p class="source" dir="auto">Source${src.startsWith("(knowledge transfer)") ? " (knowledge transfer)" : ""}: ${inline(src.replace("(knowledge transfer) ", ""))}</p>`).join("\n");
  return `<section id="${id}"${sp.dark ? ' class="dark"' : ""} aria-label="Slide ${labels[i]}">\n<h2 dir="auto"><span class="num">Slide ${labels[i]}.</span> ${inline(sp.title)}</h2>\n${banner}${htmlList(lines)}\n${figs ? `<div class="figs">${figs}</div>\n` : ""}${srcs}\n<p class="note" dir="auto">${inline(sp.note)}</p>\n</section>`;
});
const CSS = `
*{box-sizing:border-box}
body{margin:0;background:#F1F1F1;color:#1A1A1A;font:16px/1.5 Calibri,Arial,sans-serif}
section{background:#FFFFFF;color:#1A1A1A;max-width:960px;margin:16px auto;padding:24px 28px;overflow-wrap:anywhere}
section.dark{background:#111111;color:#FFFFFF}
h1{font-size:2.4em;margin:.3em 0;text-align:center}
h2{font-family:Cambria,Georgia,serif;font-size:1.7em;margin:0 0 .6em;border-bottom:3px solid #E31B23;padding-bottom:.2em}
.cover{text-align:center;padding-top:48px}
.logos{margin:0;display:flex;justify-content:center;align-items:center;gap:16px}
.slogan{color:#E31B23;font-size:1.5em;font-family:Cambria,Georgia,serif}
.banner{display:inline-block;background:#E31B23;color:#FFFFFF;font-weight:bold;padding:4px 14px;margin:0 0 .8em}
.figs{display:flex;flex-wrap:wrap;gap:12px;margin:.6em 0}
figure{margin:0;flex:1 1 300px;max-width:100%}
figure img{display:block;width:100%;height:auto;border:1px solid #111111}
.cropbox{overflow:hidden;border:1px solid #111111;aspect-ratio:var(--ar)}
.cropbox img{max-width:none;border:0}
figcaption{font-size:.75em;font-style:italic}
ul{padding-left:1.3em}li{margin:.35em 0}
code{background:#F1F1F1;color:#1A1A1A;padding:0 .25em;overflow-wrap:anywhere}
.dark code{background:#1A1A1A;color:#FFFFFF}
.source{color:#E31B23;font-size:.8em;margin:.8em 0 0}
.dark .source{color:#F1F1F1}
.note{font-size:.85em;border-left:3px solid #E31B23;padding-left:.8em;margin:1em 0 0;color:#1A1A1A}
.dark .note{color:#FFFFFF}
@page{size:A4 landscape;margin:10mm}
@media print{
body{background:#FFFFFF;font-size:11pt;line-height:1.3;-webkit-print-color-adjust:exact;print-color-adjust:exact}
section{max-width:none;margin:0;padding:6mm 8mm;break-after:page;page-break-after:always;min-height:185mm;overflow:hidden}
section:last-child{break-after:auto;page-break-after:auto}
}`;
const html = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${esc(pres.title)}</title>
<style>${CSS}</style>
</head>
<body>
<!-- Generated by make/build_pptx.js from the same spec as presentation.pptx and presentation.md. Do not edit by hand. -->
${sections.join("\n")}
</body>
</html>
`;
fs.writeFileSync(path.join(__dirname, "..", "presentation.html"), html);

fs.writeFileSync(path.join(__dirname, "..", "presentation.md"), md.join("\n"));
pres.writeFile({ fileName: path.join(__dirname, "..", "presentation.pptx") }).then(() => {
  console.log("slides:", slides.length, "warnings:", warnings.length);
  warnings.forEach((w) => console.log("WARN", w));
});
