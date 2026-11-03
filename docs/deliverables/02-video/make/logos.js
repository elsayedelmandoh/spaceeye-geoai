// Render the logo overlay: a transparent 1920x1080 PNG laid over every shot.
// Top left: digilians-program, ACUD_logo. Top right: MCIT, Egyptian_Military_Academy.
// Each logo sits on a white rounded backdrop so it stays readable on dark and photo frames.
// Run: NODE_PATH=<dir with playwright> node logos.js <out_dir>
const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const OUT = process.argv[2] || path.join(__dirname, "out");
const ROOT = path.join(__dirname, "..");
const LOGO_H = 80, PAD = 8, MARGIN = 36, GAP = 20, RADIUS = 10;

// data URIs: the page is about:blank, so file:// images would be blocked.
const logo = (f) =>
  `<img src="data:image/png;base64,${fs.readFileSync(path.join(ROOT, f)).toString("base64")}">`;

const css = `html,body{margin:0;width:1920px;height:1080px;background:transparent;position:relative;overflow:hidden}
.row{position:absolute;top:${MARGIN}px;display:flex;gap:${GAP}px}.l{left:${MARGIN}px}.r{right:${MARGIN}px}
.row img{height:${LOGO_H}px;width:auto;display:block;box-sizing:content-box;padding:${PAD}px;background:#fff;border-radius:${RADIUS}px;box-shadow:0 2px 8px rgba(0,0,0,.35)}`;
const html = `<div class="row l">${logo("digilians-program.png")}${logo("ACUD_logo.png")}</div>
<div class="row r">${logo("MCIT.png")}${logo("Egyptian_Military_Academy.png")}</div>`;

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  await page.setContent(`<html><head><meta charset="utf-8"><style>${css}</style></head><body>${html}</body></html>`);
  await page.screenshot({ path: path.join(OUT, "logos.png"), omitBackground: true });
  await browser.close();
})().catch((err) => { console.error(err); process.exit(1); });
