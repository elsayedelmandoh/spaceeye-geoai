// Render the title and end cards (1920x1080 PNG) from the text files in ./text.
// Chromium shapes Arabic correctly, which ffmpeg drawtext does not.
// Run: NODE_PATH=<dir with playwright> node cards.js <out_dir>
const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const HERE = __dirname;
const OUT = process.argv[2] || path.join(HERE, "out");
const text = (name) => fs.readFileSync(path.join(HERE, "text", name), "utf8").trim();
const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
const lines = (s) => esc(s).split("\n").join("<br>");

const css = `body{margin:0;width:1920px;height:1080px;display:flex;flex-direction:column;justify-content:center;align-items:center;
background:radial-gradient(circle at 50% 40%,#16314f,#070d18);color:#fff;font-family:'Noto Naskh Arabic','Noto Sans Arabic','DejaVu Sans',sans-serif;text-align:center}
.en{font:700 96px/1.1 'DejaVu Sans',sans-serif;letter-spacing:2px}.ar{font-size:64px;margin-top:28px;direction:rtl}
.small{font-size:30px;color:#c9d3e0;margin-top:40px;direction:auto}.tiny{position:absolute;bottom:40px;font:24px 'DejaVu Sans',sans-serif;color:#8796ab}`;

const cards = {
  title: `<div class="en">${esc(text("title_brand.txt"))}</div>
          <div class="ar">${lines(text("title_headline.txt"))}</div>
          <div class="small">${lines(text("title_credits.txt"))}</div>`,
  end: `<div class="ar" style="font-size:80px">${lines(text("end_slogan.txt"))}</div>
        <div class="en" style="font-size:64px;margin-top:36px">${esc(text("title_brand.txt"))}</div>
        <div class="tiny">${esc(text("end_note.txt"))}</div>`,
};

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  for (const [name, html] of Object.entries(cards)) {
    await page.setContent(`<html><head><meta charset="utf-8"><style>${css}</style></head><body>${html}</body></html>`);
    await page.screenshot({ path: path.join(OUT, `${name}.png`) });
  }
  await browser.close();
})().catch((err) => { console.error(err); process.exit(1); });
