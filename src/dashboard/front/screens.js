// SpaceEye light table: screens 1 (priority) and 2 (compound file).
// Draws only what the page sends; every number comes from the stored files.

const DECK_URL = "https://unpkg.com/deck.gl@9.1.14/dist.min.js";
const TILES = "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}";
const LEVEL_VAR = { 1: "--l1", 2: "--l2", 3: "--l3", 4: "--l4" };
const LEVEL_RGB = { 1: [168, 16, 44], 2: [227, 93, 23], 3: [209, 168, 12], 4: [46, 125, 79] };
const NA_RGB = [138, 143, 139];
const SEL_RGB = [0, 124, 137];
const HEIGHT_SCALE = 10;
const memory = new WeakMap();
let deckPromise = null;

function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v === null || v === undefined || v === false) continue;
    if (k === "text") node.textContent = v;
    else if (k === "style") node.style.cssText = v;
    else if (k.startsWith("on")) node.addEventListener(k.slice(2), v);
    else node.setAttribute(k, v === true ? "" : v);
  }
  for (const child of children.flat()) {
    if (child === null || child === undefined || child === false) continue;
    node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return node;
}

function svg(tag, attrs = {}) {
  const node = document.createElementNS("http://www.w3.org/2000/svg", tag);
  for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
  return node;
}

// Arabic counted noun after a digit: 3-10 take the plural, 11-99 the accusative singular.
function countAr(n, one, few, many) {
  const rest = n % 100;
  return rest >= 3 && rest <= 10 ? few : rest >= 11 ? many : one;
}
const months = (n) => `${n} ${countAr(n, "شهر", "أشهر", "شهرًا")}`;
const code = (c) => el("bdi", { text: c });

// The stored inspection file opens in a new tab, ready to print; if the tab is blocked it downloads.
function fileButton(file, label, cls = "lt-link") {
  if (!file) return null;
  return el("button", { class: cls, type: "button", onclick: () => {
    const url = URL.createObjectURL(new Blob([file.html], { type: "text/html;charset=utf-8" }));
    if (!window.open(url, "_blank")) el("a", { href: url, download: file.name }).click();
    setTimeout(() => URL.revokeObjectURL(url), 60000);
  } }, label);
}

function level(levelNumber, word) {
  const v = LEVEL_VAR[levelNumber];
  return el("span", { class: "lt-level", style: v ? `--c: var(${v})` : null }, el("i"), word);
}

function loadDeck() {
  if (window.deck) return Promise.resolve(window.deck);
  deckPromise ||= new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = DECK_URL;
    script.onload = () => resolve(window.deck);
    script.onerror = () => { deckPromise = null; reject(new Error("deck.gl did not load")); };
    document.head.append(script);
  });
  return deckPromise;
}

// ---------------------------------------------------------------- screen 1 --

function printBlock(item, onOpen) {
  const frames = item.frames;
  let index = frames.length - 1;
  const img = el("img", { src: frames[index].src, alt: "" });
  const frame = el("div", { class: "lt-frame" }, img);
  const foot = el("img", { class: "lt-foot", alt: "" });
  const date = el("span");
  const stage = el("span");
  const head = el("div", { class: "lt-label" },
    el("strong", { text: item.code }), date, stage,
    el("span", { class: "lt-open" },
      el("button", { class: "lt-link", type: "button", onclick: () => onOpen(item.code) },
        "افتح ملف ", code(item.code))));
  const buttons = frames.map((f, i) => el("button", {
    type: "button", "aria-pressed": "false",
    "aria-label": `${item.code}، صورة ${f.date}`,
    onclick: () => show(i), onmouseenter: () => show(i),
  }, el("img", { src: f.src, alt: "" }), el("span", { class: "d", text: f.date }),
     el("span", { class: "s", text: f.stage || "المرحلة مش مسجلة" })));

  function show(i) {
    if (i === index && img.dataset.ready) return;
    index = i;
    img.dataset.ready = "1";
    const next = el("img", { src: frames[i].src, alt: `${item.code} من الفضاء، صورة ${frames[i].date}`, class: "is-next" });
    frame.append(next);
    requestAnimationFrame(() => next.classList.add("is-on"));
    setTimeout(() => { [...frame.querySelectorAll("img")].slice(0, -1).forEach((n) => n.remove()); }, 220);
    foot.hidden = !frames[i].foot;
    if (frames[i].foot) { foot.src = frames[i].foot; foot.alt = `بيانات صورة ${frames[i].date}`; }
    date.replaceChildren("صورة ", code(frames[i].date));
    stage.textContent = frames[i].stage || "";
    buttons.forEach((b, j) => b.setAttribute("aria-pressed", String(j === i)));
  }

  const strip = el("ol", {
    class: "lt-strip", "aria-label": "تواريخ الصور، الأقدم الأول",
    onkeydown: (e) => {
      if (e.key === "ArrowRight" && index < frames.length - 1) { show(index + 1); buttons[index].focus(); }
      if (e.key === "ArrowLeft" && index > 0) { show(index - 1); buttons[index].focus(); }
    },
  }, buttons.map((b) => el("li", {}, b)));
  show(index);
  return el("figure", { class: "lt-print" }, el("div", { class: "lt-mat" }, frame, foot, head), strip);
}

function renderPriority(root, data, ctx) {
  const state = memory.get(ctx.parentElement) || {};
  const cycle = data.cycle;
  const codes = cycle.map((c) => c.code);
  let selected = codes.includes(state.selected) ? state.selected : codes[0];

  const head = el("header", { class: "lt-head" },
    el("h1", {}, cycle.length
      ? ["زور ", el("b", {}, joinCodes(codes)), " الدورة دي"]
      : ["مفيش كمباوند محتاج زيارة الدورة دي"]),
    el("p", { class: "lt-sub" },
      el("span", {}, `${cycle.length} من ${data.total} كمباوند في `, code("R7")),
      el("span", {}, "بيانات ", code(data.asof))));
  root.append(head);
  if (!cycle.length) return;

  const printSlot = el("div");
  const rows = cycle.map((item) => el("button", {
    type: "button", "aria-pressed": "false",
    onclick: () => select(item.code),
  }, el("span", { class: "rank", text: item.rank }), el("bdi", { class: "code", text: item.code }),
     level(item.level, item.level_word), el("span", { class: "why", text: item.why })));
  const list = el("ol", { class: "lt-visits", "aria-label": "ترتيب الزيارات" }, rows.map((r, i) => el("li", {}, r,
    fileButton(cycle[i].file, ["ملف التفتيش لـ ", code(cycle[i].code)], "lt-link lt-row-file"))));
  const side = el("aside", { class: "lt-side" }, el("h2", { text: "ترتيب الزيارات" }), list);
  if (data.waiting > 0) {
    side.append(el("p", { class: "lt-wait", text: `و${data.waiting} كمباوند كمان مستنيين الدورة الجاية.` }));
  }
  const credit = el("p", { class: "lt-credit", text: data.credit });
  root.append(el("div", { class: "lt-grid" }, el("div", {}, printSlot, credit), side));

  let mapApi = null;
  if (data.map) mapApi = mapBlock(side, data, ctx, (code) => (codes.includes(code) ? select(code) : ctx.open(code)));

  function select(code) {
    selected = code;
    memory.set(ctx.parentElement, { ...state, selected: code });
    rows.forEach((r, i) => r.setAttribute("aria-pressed", String(codes[i] === code)));
    const item = cycle.find((c) => c.code === code);
    printSlot.replaceChildren(item.frames.length
      ? printBlock(item, ctx.open)
      : el("p", { class: "lt-empty", text: `مفيش صور Wayback مختارة لـ ${code}.` }));
    mapApi?.highlight(code);
  }
  select(selected);
  return () => mapApi?.destroy();
}

function joinCodes(codes) {
  const parts = codes.map(code);
  if (parts.length < 2) return parts;
  return [...parts.slice(0, -1).flatMap((c, i) => (i ? ["، ", c] : [c])), " و", parts[parts.length - 1]];
}

function mapBlock(side, data, ctx, onPick) {
  const holder = el("div", { class: "lt-map", role: "img", "aria-label": "خريطة كمباوندات R7 ملوّنة حسب الأولوية" });
  const tilt = el("button", { class: "lt-chip-btn", type: "button", "aria-pressed": "false", text: "عرض 3D" });
  const wrap = el("div", { class: "lt-map-wrap" }, holder,
    el("div", { class: "lt-map-tools" }, tilt),
    el("div", { class: "lt-map-attr", text: "Basemap: Esri, HERE, Garmin, © OpenStreetMap contributors" }));
  const legend = el("ul", { class: "lt-legend" },
    data.legend.map((l) => el("li", {}, level(l.level, `${l.word} · ${l.count}`))));
  side.append(el("h2", { text: "أماكنهم" }), wrap, legend,
    el("p", { class: "lt-note", text: data.map_note }));

  let deckInstance = null;
  let highlighted = null;
  let tilted = false;
  let dead = false;

  const features = data.compounds.map((c) => ({
    type: "Feature", geometry: c.geometry,
    properties: c,
  }));
  const points = features.flatMap((f) => flatten(f.geometry.coordinates));
  const lon = points.map((p) => p[0]);
  const lat = points.map((p) => p[1]);
  const bounds = [[Math.min(...lon), Math.min(...lat)], [Math.max(...lon), Math.max(...lat)]];

  function layers(deck) {
    return [
      new deck.TileLayer({
        id: "base", data: TILES, minZoom: 0, maxZoom: 16, tileSize: 256,
        renderSubLayers: (props) => {
          const [[w, s], [e, n]] = props.tile.boundingBox;
          return new deck.BitmapLayer(props, { data: null, image: props.data, bounds: [w, s, e, n] });
        },
      }),
      new deck.GeoJsonLayer({
        id: "compounds", data: { type: "FeatureCollection", features },
        filled: true, stroked: true, extruded: tilted, wireframe: tilted, pickable: true,
        getFillColor: (f) => [...(LEVEL_RGB[f.properties.level] || NA_RGB), f.properties.code === highlighted ? 215 : 150],
        getLineColor: (f) => (f.properties.code === highlighted ? [...SEL_RGB, 255] : [255, 255, 255, 230]),
        getLineWidth: (f) => (f.properties.code === highlighted ? 3 : 1.2),
        lineWidthUnits: "pixels",
        getElevation: (f) => (f.properties.height || 0) * HEIGHT_SCALE,
        updateTriggers: { getFillColor: highlighted, getLineColor: highlighted, getLineWidth: highlighted },
        onClick: ({ object }) => object && onPick(object.properties.code),
      }),
      new deck.TextLayer({
        id: "codes", data: data.compounds.filter((c) => c.rank),
        getPosition: (c) => [...c.center, tilted ? (c.height || 0) * HEIGHT_SCALE + 30 : 0],
        getText: (c) => String(c.rank),
        getSize: 14, getColor: [255, 255, 255, 255],
        fontFamily: "Readex Pro, Segoe UI, sans-serif", fontWeight: 600,
        background: true, getBackgroundColor: (c) => (c.code === highlighted ? [...SEL_RGB, 255] : [26, 29, 27, 235]),
        backgroundPadding: [6, 3],
        characterSet: "auto", billboard: true,
        updateTriggers: { getPosition: tilted, getBackgroundColor: highlighted },
      }),
    ];
  }

  function draw() { if (deckInstance && window.deck) deckInstance.setProps({ layers: layers(window.deck) }); }

  loadDeck().then((deck) => {
    if (dead) return;
    const width = holder.clientWidth || 400;
    const height = holder.clientHeight || 330;
    const view = new deck.WebMercatorViewport({ width, height }).fitBounds(bounds, { padding: 28 });
    deckInstance = new deck.Deck({
      parent: holder,
      initialViewState: { longitude: view.longitude, latitude: view.latitude, zoom: view.zoom, pitch: 0, bearing: 0 },
      controller: { scrollZoom: false, dragRotate: true },
      layers: layers(deck),
      getCursor: ({ isHovering }) => (isHovering ? "pointer" : "grab"),
      getTooltip: ({ object }) => object && {
        html: `<b>${object.properties.code}</b> · ${object.properties.level_word}<br>${object.properties.height_text}<br>` +
          (object.properties.rank ? "اضغط تشوفه من الفضاء" : "اضغط تفتح ملفه"),
        style: { direction: "rtl", background: "#1a1d1b", color: "#fff", fontFamily: "Readex Pro, sans-serif", fontSize: "12px",
          padding: "6px 8px", borderRadius: "3px" },
      },
    });
    tilt.addEventListener("click", () => {
      tilted = !tilted;
      tilt.setAttribute("aria-pressed", String(tilted));
      deckInstance.setProps({
        initialViewState: {
          longitude: view.longitude, latitude: view.latitude, zoom: view.zoom,
          pitch: tilted ? 50 : 0, bearing: tilted ? -18 : 0,
          transitionDuration: 600, transitionInterpolator: new deck.FlyToInterpolator(),
        },
        layers: layers(deck),
      });
    });
  }).catch(() => {
    holder.replaceChildren(el("p", { class: "lt-empty", text: "الخريطة محتاجة اتصال بالإنترنت." }));
  });

  return {
    highlight(code) { highlighted = code; draw(); },
    destroy() { dead = true; deckInstance?.finalize(); },
  };
}

function flatten(coords) {
  return typeof coords[0] === "number" ? [coords] : coords.flatMap(flatten);
}

// ---------------------------------------------------------------- screen 2 --

function renderCompound(root, data) {
  root.append(el("header", { class: "lt-head" },
    el("div", { class: "lt-head-row" }, el("h1", {}, data.code, level(data.level, data.level_word)),
      fileButton(data.file, "اطبع ملف الزيارة", "lt-print-btn")),
    data.reason_ar ? el("p", { class: "lt-reason", text: data.reason_ar }) : null,
    el("p", { class: "lt-sub" }, el("span", {}, "بيانات ", code(data.asof)))));

  const left = el("div", {}, data.frames.length >= 2 ? swipeBlock(data) :
    el("p", { class: "lt-empty", text: `أقل من صورتين Wayback لـ ${data.code}، فمفيش مقارنة.` }),
    el("p", { class: "lt-credit", text: data.credit }));
  const right = el("aside", { class: "lt-side" },
    el("h2", { text: "ليه في الأولوية دي" }), clocks(data.clocks),
    el("h2", { text: "نشاط البناء كل ربع" }), activityChart(data),
    el("h2", { class: "lt-section", text: "مرحلة الإنشاء كل سنة" }), stageBand(data));
  root.append(el("div", { class: "lt-grid" }, left, right));
  if (data.promises.length) {
    root.append(el("section", { class: "lt-band" },
      el("h2", { class: "lt-band-title", text: "المطور قال، والفضاء شاف" }),
      el("p", { class: "lt-sub", text: "تصريحات المطور المنشورة، وجنب كل واحد أقرب صورة من الفضاء ومرحلة الإنشاء." }),
      promiseList(data.promises, data.frames)));
  }
}

// One row per published claim; the picture shows only when it differs from the row above.
function promiseList(rows, frames) {
  let shown = null;
  return el("ol", { class: "lt-promises" }, rows.map((r) => {
    const f = r.frame === null ? null : frames[r.frame];
    const fresh = f && r.frame !== shown;
    if (f) shown = r.frame;
    const due = r.due ? el("p", { class: "lt-due" }, r.due.passed
      ? `الموعد عدّى. الفضاء سنة ${r.due.year}: ${r.due.stage || "مفيش مرحلة مسجلة"}`
      : `الموعد لسه ما جاش (${r.due.year}).`) : null;
    return el("li", {},
      el("span", { class: "lt-said", text: r.said }),
      el("div", {}, el("p", { class: "lt-claim", text: r.claim }), due),
      fresh ? el("figure", { class: "lt-thumb" }, el("img", { src: f.src, alt: `صورة ${f.date}` }),
        el("figcaption", {}, code(f.date), f.stage ? ` · ${f.stage}` : ""))
        : f ? el("span") : el("p", { class: "lt-thumb-note", text: `مفيش صورة قريبة. مرحلة السنة: ${r.stage || "غير مسجلة"}` }));
  }));
}

function swipeBlock(data) {
  const frames = data.frames;
  let before = 0;
  let after = frames.length - 1;
  const imgBefore = el("img", { alt: "" });
  const imgAfter = el("img", { class: "lt-after", alt: "" });
  const tagLeft = el("span", { class: "lt-tag left" });
  const tagRight = el("span", { class: "lt-tag right" });
  const frame = el("div", { class: "lt-frame", style: "--cut: 50%" }, imgBefore, imgAfter, el("div", { class: "lt-divider" }), tagLeft, tagRight);
  const range = el("input", { class: "lt-range", type: "range", min: 0, max: 100, value: 50, "aria-label": "حرّك الفاصل بين الصورتين" });
  const cut = (pct) => { frame.style.setProperty("--cut", `${pct}%`); range.value = Math.round(pct); };
  range.addEventListener("input", () => cut(Number(range.value)));
  let dragging = false;
  const fromEvent = (e) => {
    const box = frame.getBoundingClientRect();
    cut(Math.min(100, Math.max(0, ((e.clientX - box.left) / box.width) * 100)));
  };
  frame.addEventListener("pointerdown", (e) => { dragging = true; frame.setPointerCapture(e.pointerId); fromEvent(e); });
  frame.addEventListener("pointermove", (e) => dragging && fromEvent(e));
  frame.addEventListener("pointerup", () => { dragging = false; });

  const option = (f, i) => el("option", { value: i, text: f.stage ? `${f.date} · ${f.stage}` : f.date });
  const selBefore = el("select", { "aria-label": "تاريخ الصورة الشمال" }, frames.map(option));
  const selAfter = el("select", { "aria-label": "تاريخ الصورة اليمين" }, frames.map(option));
  function paint() {
    imgBefore.src = frames[before].src;
    imgBefore.alt = `${data.code}، صورة ${frames[before].date}`;
    imgAfter.src = frames[after].src;
    imgAfter.alt = `${data.code}، صورة ${frames[after].date}`;
    tagLeft.textContent = frames[before].date;
    tagRight.textContent = frames[after].date;
    selBefore.value = before;
    selAfter.value = after;
  }
  selBefore.addEventListener("change", () => { before = Number(selBefore.value); paint(); });
  selAfter.addEventListener("change", () => { after = Number(selAfter.value); paint(); });
  paint();

  const feet = el("div", { class: "lt-feet" });
  function credits() {
    feet.replaceChildren(...[["الشمال", before], ["اليمين", after]].filter(([, i]) => frames[i].foot).map(([side, i]) =>
      el("div", {}, el("span", {}, `${side} · `, code(frames[i].date)),
        el("img", { src: frames[i].foot, alt: `بيانات صورة ${frames[i].date}` }))));
  }
  selBefore.addEventListener("change", credits);
  selAfter.addEventListener("change", credits);
  credits();
  return el("figure", { class: "lt-print lt-swipe" },
    el("div", { class: "lt-mat" }, frame,
      el("div", { class: "lt-label" }, el("strong", { text: data.code }),
        el("span", { text: "اسحب على الصورة عشان تقارن بين تاريخين" }))),
    range,
    el("div", { class: "lt-pickers" },
      el("label", {}, "الشمال ", selBefore), el("label", {}, "اليمين ", selAfter)),
    feet);
}

function clocks(rows) {
  return el("dl", { class: "lt-clocks" }, rows.map((r) => {
    const cls = r.text ? "is-text" : (r.value === 0 ? "is-zero" : null);
    return el("div", {},
      el("dt", {}, r.label, el("small", { text: r.rule })),
      el("dd", { class: cls }, r.text ?? r.value, r.text ? null : el("small", { text: r.unit })));
  }));
}

function activityChart(data) {
  const rows = data.quarters;
  const box = el("div", { class: "lt-chart" });
  const tip = el("div", { class: "lt-tip", hidden: true });
  const keys = el("ul", { class: "lt-keys" },
    el("li", {}, el("i", { style: "--c: var(--series-a)" }), "درجة النشاط ", code("A")),
    el("li", {}, el("i", { style: "--c: var(--series-dw)" }), "احتمال البناء ", code("Dynamic World")),
    data.statements.length ? el("li", {}, el("i", { class: "tri" }), "المطور نشر تصريح") : null);
  if (!rows.length) return el("p", { class: "lt-empty", text: "مفيش بيانات ربع سنوية." });

  const H = 210;
  const pad = { l: 30, r: 44, t: 18, b: 24 };
  function draw() {
    const W = Math.max(box.clientWidth || 420, 280);
    const x = (i) => pad.l + (rows.length === 1 ? 0 : (i / (rows.length - 1)) * (W - pad.l - pad.r));
    const y = (v) => pad.t + (1 - v) * (H - pad.t - pad.b);
    const s = svg("svg", { viewBox: `0 0 ${W} ${H}`, height: H, role: "img",
      "aria-label": `درجة النشاط واحتمال البناء لـ ${data.code} من ${rows[0].q} لـ ${rows[rows.length - 1].q}` });
    for (const v of [0, 0.5, 1]) {
      s.append(svg("line", { x1: pad.l, x2: W - pad.r, y1: y(v), y2: y(v), stroke: "#e6e9e3", "stroke-width": 1 }));
      const t = svg("text", { x: pad.l - 6, y: y(v) + 4, "text-anchor": "end" }); t.textContent = v.toFixed(1); s.append(t);
    }
    const years = rows.map((r, i) => [r.q.slice(0, 4), i]).filter(([, i]) => rows[i].q.endsWith("Q1"));
    const step = years.length > 8 ? 2 : 1;
    years.forEach(([yr, i], k) => {
      if (k % step) return;
      const t = svg("text", { x: x(i), y: H - 6, "text-anchor": "middle" }); t.textContent = yr; s.append(t);
    });
    // Events: developer statements as small marks on the top edge; the first handover date as a labelled rule.
    for (const q of data.statements) {
      const i = rows.findIndex((r) => r.q === q);
      if (i < 0) continue;
      s.append(svg("path", { d: `M${x(i) - 5},${pad.t - 12} h10 l-5,7 z`, fill: "#4f5652" }));
    }
    if (data.deadline) {
      const i = rows.findIndex((r) => r.q === data.deadline.q);
      if (i >= 0) {
        s.append(svg("line", { x1: x(i), x2: x(i), y1: pad.t, y2: H - pad.b, stroke: "#1a1d1b", "stroke-width": 1 }));
        const t = svg("text", { x: x(i) + 5, y: H - pad.b - 6, class: "mark-label" });
        t.textContent = `أول موعد تسليم ${data.deadline.label}`; s.append(t);
      }
    }
    for (const [key, color, name] of [["dw", "#b8860b", "DW"], ["a", "#2b59c3", "A"]]) {
      let d = "";
      let pen = false;
      rows.forEach((r, i) => {
        if (r[key] === null) { pen = false; return; }
        d += `${pen ? "L" : "M"}${x(i).toFixed(1)},${y(r[key]).toFixed(1)}`;
        pen = true;
      });
      s.append(svg("path", { d, fill: "none", stroke: color, "stroke-width": 2, "stroke-linejoin": "round", "stroke-linecap": "round" }));
      const last = rows.map((r, i) => [r[key], i]).filter(([v]) => v !== null).pop();
      if (last) {
        s.append(svg("circle", { cx: x(last[1]), cy: y(last[0]), r: 4, fill: color, stroke: "#fff", "stroke-width": 2 }));
        const t = svg("text", { x: x(last[1]) + 8, y: y(last[0]) + 4, class: "end" });
        t.textContent = `${name} ${last[0].toFixed(2)}`; s.append(t);
      }
    }
    const cross = svg("line", { y1: pad.t, y2: H - pad.b, stroke: "#6d746f", "stroke-width": 1, visibility: "hidden" });
    const dotA = svg("circle", { r: 4, fill: "#2b59c3", stroke: "#fff", "stroke-width": 2, visibility: "hidden" });
    const dotD = svg("circle", { r: 4, fill: "#b8860b", stroke: "#fff", "stroke-width": 2, visibility: "hidden" });
    const hit = svg("rect", { x: pad.l, y: 0, width: W - pad.l - pad.r, height: H, fill: "transparent" });
    s.append(cross, dotD, dotA, hit);
    hit.addEventListener("pointermove", (e) => {
      const bx = s.getBoundingClientRect();
      const px = ((e.clientX - bx.left) / bx.width) * W;
      const i = Math.round(((px - pad.l) / (W - pad.l - pad.r)) * (rows.length - 1));
      const r = rows[Math.max(0, Math.min(rows.length - 1, i))];
      const xi = x(rows.indexOf(r));
      cross.setAttribute("x1", xi); cross.setAttribute("x2", xi); cross.setAttribute("visibility", "visible");
      for (const [dot, v] of [[dotA, r.a], [dotD, r.dw]]) {
        dot.setAttribute("visibility", v === null ? "hidden" : "visible");
        if (v !== null) { dot.setAttribute("cx", xi); dot.setAttribute("cy", y(v)); }
      }
      const fmt = (v) => (v === null ? "غير متاح" : v.toFixed(2));
      tip.innerHTML = "";
      tip.append(el("b", { text: r.q }), ` · A ${fmt(r.a)} · DW ${fmt(r.dw)}`,
        data.statements.includes(r.q) ? " · تصريح منشور" : "");
      tip.style.left = `${(xi / W) * 100}%`;
      tip.style.top = `${pad.t}px`;
      tip.hidden = false;
    });
    hit.addEventListener("pointerleave", () => {
      tip.hidden = true;
      [cross, dotA, dotD].forEach((n) => n.setAttribute("visibility", "hidden"));
    });
    box.replaceChildren(s, tip);
  }
  const observer = new ResizeObserver(() => draw());
  observer.observe(box);
  requestAnimationFrame(draw);

  const table = el("details", {}, el("summary", { text: "القيم في جدول" }),
    el("table", {}, el("thead", {}, el("tr", {}, el("th", { text: "الربع" }), el("th", { text: "A" }), el("th", { text: "DW" }))),
      el("tbody", {}, rows.map((r) => el("tr", {}, el("td", { text: r.q }),
        el("td", { text: r.a === null ? "—" : r.a.toFixed(2) }), el("td", { text: r.dw === null ? "—" : r.dw.toFixed(2) }))))));
  return el("div", {}, keys, box, data.chart_note ? el("p", { class: "lt-note", text: data.chart_note }) : null, table);
}

function stageBand(data) {
  const stages = data.stages;
  if (!stages.length) return el("p", { class: "lt-empty", text: data.stage_missing || "مفيش مراحل مسجلة." });
  const color = { S0: "var(--s0)", S1: "var(--s1)", S2: "var(--s2)" };
  const band = el("div", { class: "lt-band-years", style: `display:grid;grid-template-columns:repeat(${stages.length},minmax(0,1fr));gap:2px` },
    stages.map((s) => el("div", { title: `${s.year}: ${s.word}` },
      el("div", { style: `height:22px;border-radius:2px;background:${color[s.stage] || "var(--l0)"}` }),
      el("div", { style: "font-size:11px;color:var(--ink-3);text-align:center;margin-top:3px;font-variant-numeric:tabular-nums", text: `'${String(s.year).slice(2)}` }))));
  const keys = el("ul", { class: "lt-keys", style: "margin-top:8px" }, data.stage_words.map((w) =>
    el("li", {}, el("i", { class: "sq", style: `--c: ${color[w.stage]}` }), w.word)));
  return el("div", {}, band, keys, el("p", { class: "lt-note", text: data.stage_note }));
}

// ---------------------------------------------------------------- screen 4 --

function renderValue(root, data, ctx) {
  root.append(el("header", { class: "lt-head" },
    el("h1", {}, code("SpaceEye"), " بيقدّم إيه للجنة"),
    el("p", { class: "lt-sub" }, el("span", {}, `${data.total} كمباوند في `, code("R7")), el("span", {}, "بيانات ", code(data.asof)))));

  const ex = data.example;
  if (ex || data.now.length) {
    const story = ex ? el("div", { class: "lt-story" },
      el("p", { class: "lt-lead" }, "في ", code(ex.alert), "، كان ", code("SpaceEye"), " هينبّه على ", el("b", {}, code(ex.code)),
        `، قبل أول موعد تسليم له (${ex.deadline}) بـ ${months(ex.months)}.`),
      el("p", {}, `اللي اتشاف من الفضاء: ${ex.why}.`),
      el("p", {}, `اللي حصل${ex.reported ? ` (اتنشر ${ex.reported})` : ""}: ${ex.outcome}.`)) : null;
    const prints = ex ? el("div", { class: "lt-pair" }, ex.frames.map((f, i) => el("figure", { class: "lt-mat" },
      el("img", { class: "lt-pair-img", src: f.src, alt: `${ex.code} من الفضاء، صورة ${f.date}` }),
      f.foot ? el("img", { class: "lt-foot", src: f.foot, alt: `بيانات صورة ${f.date}` }) : null,
      el("figcaption", { class: "lt-label" }, el("strong", { text: f.date }),
        el("span", { text: i === 0 && ex.frames.length > 1 ? "بعد أول تنبيه" : "آخر صورة" }))))) : null;
    const nowList = data.now.length ? el("div", {},
      el("h3", { class: "lt-h3", text: "عليهم تنبيه دلوقتي، قبل ما أي موعد تسليم يعدّي" }),
      el("ul", { class: "lt-now" }, data.now.map((n) => el("li", {},
        el("bdi", { class: "code", text: n.code }), level(n.level, n.level_word),
        el("span", { class: "why", text: n.why }),
        el("button", { class: "lt-link", type: "button", onclick: () => ctx.open(n.code) }, "افتح ملف ", code(n.code)))))) : null;
    root.append(el("section", { class: "lt-band" },
      el("h2", { class: "lt-band-title", text: "بينبّه قبل ما الميعاد يعدّي" }),
      el("div", { class: "lt-grid lt-grid-story" }, el("div", {}, story, nowList), prints)));
  }

  const pr = data.promise;
  if (pr) {
    const progress = pr.claims.filter((c) => c.claim.startsWith("نسبة"));
    root.append(el("section", { class: "lt-band" },
      el("h2", { class: "lt-band-title", text: "المطور قال، والفضاء شاف" }),
      el("div", { class: "lt-grid lt-grid-story" },
        el("div", { class: "lt-story" },
          el("p", { class: "lt-lead" }, el("b", {}, code(pr.code)), progress.length
            ? `: المطور قال ${progress.map((c) => `${c.claim.replace("نسبة التنفيذ ", "")} في ${c.said}`).join("، ثم ")}.`
            : ": تصريحات المطور المنشورة."),
          el("ul", { class: "lt-claims" }, pr.claims.filter((c) => c.due).map((c) => el("li", {},
            `${c.claim} (اتنشر ${c.said}). `, c.due.passed ? `الفضاء سنة ${c.due.year}: ${c.due.stage || "غير مسجلة"}.` : "الموعد لسه ما جاش."))),
          el("p", {}, `النهارده عدّى ${months(pr.k3)} على أول موعد تسليم معلن.`),
          el("button", { class: "lt-link", type: "button", onclick: () => ctx.open(pr.code) }, "افتح ملف ", code(pr.code))),
        el("div", { class: "lt-pair" }, pr.frames.map((f) => el("figure", { class: "lt-mat" },
          el("img", { class: "lt-pair-img", src: f.src, alt: `${pr.code} من الفضاء، صورة ${f.date}` }),
          f.foot ? el("img", { class: "lt-foot", src: f.foot, alt: `بيانات صورة ${f.date}` }) : null,
          el("figcaption", { class: "lt-label" }, el("strong", { text: f.date }),
            el("span", { text: f.stage ? `${f.caption} · ${f.stage}` : f.caption }))))))));
  }

  if (data.fines.length) {
    const max = Math.max(...data.fines.map((f) => f.months));
    root.append(el("section", { class: "lt-band" },
      el("h2", { class: "lt-band-title" }, `${months(data.fine_months)} تأخير ممكن تتحسب عليها غرامة`),
      el("p", { class: "lt-sub", text: `في ${data.fines.length} كمباوندات، محسوبة من مواعيد التسليم المنشورة. العقد هو اللي بيحدد الغرامة.` }),
      el("ol", { class: "lt-bars", "aria-label": "أشهر التأخير اللي ممكن تتحسب عليها غرامة، لكل كمباوند" },
        data.fines.map((f) => el("li", {},
          el("bdi", { class: "code", text: f.code }),
          el("span", { class: "track" }, el("span", { class: "bar", style: `width:${(f.months / max) * 100}%` })),
          el("span", { class: "val", text: months(f.months) }))))));
  }
}

// ---------------------------------------------------------------- entry --

export default function (component) {
  const { data, parentElement, setTriggerValue } = component;
  const root = el("div", { class: "lt", dir: "rtl", lang: "ar" });
  const old = parentElement.querySelector(".lt");
  if (old) old.replaceWith(root);
  else parentElement.append(root);
  if (!data) return undefined;
  const ctx = { parentElement, open: (code) => setTriggerValue("open", code) };
  if (data.screen === "priority") return renderPriority(root, data, ctx);
  if (data.screen === "value") { renderValue(root, data, ctx); return undefined; }
  renderCompound(root, data);
  return undefined;
}
