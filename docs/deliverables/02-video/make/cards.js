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
background:radial-gradient(circle at 50% 40%,#232323,#111111);color:#fff;font-family:'Noto Naskh Arabic','Noto Sans Arabic','DejaVu Sans',sans-serif;text-align:center}
.en{font:700 96px/1.1 'DejaVu Sans',sans-serif;letter-spacing:2px;border-bottom:8px solid #E31B23;padding-bottom:16px}.ar{font-size:64px;margin-top:28px;direction:rtl}
.small{font:32px/1.6 'DejaVu Sans',sans-serif;color:#F1F1F1;margin-top:40px;direction:ltr;max-width:1760px}.tiny{position:absolute;bottom:40px;font:24px 'DejaVu Sans',sans-serif;color:#B5B5B5}`;

const cards = {
  title: `<div class="en">${esc(text("title_brand.txt"))}</div>
          <div class="ar">${lines(text("title_headline.txt"))}</div>
          <div class="small">${lines(text("title_credits.txt"))}</div>`,
  end: `<div class="ar" style="font-size:80px">${lines(text("end_slogan.txt"))}</div>
        <div class="en" style="font-size:64px;margin-top:36px">${esc(text("title_brand.txt"))}</div>
        <div class="tiny">${esc(text("end_note.txt"))}</div>`,
  vision: `<div class="ar" style="font-size:88px;color:#fff;border-bottom:8px solid #E31B23;padding-bottom:18px">${lines(text("vision_title.txt"))}</div>
           <div class="ar" style="font-size:52px;color:#F1F1F1;margin-top:40px;max-width:1600px">${lines(text("vision_line.txt"))}</div>`,
};

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  for (const [name, html] of Object.entries(cards)) {
    await page.setContent(`<html><head><meta charset="utf-8"><style>${css}</style></head><body>${html}</body></html>`);
    await page.screenshot({ path: path.join(OUT, `${name}.png`) });
  }
  // Transparent lower-third caption laid over the inserted interview clips.
  const caption = `<div style="position:absolute;right:64px;bottom:72px;max-width:1500px;direction:rtl;text-align:right;
    background:rgba(17,17,17,.82);border-right:8px solid #E31B23;padding:18px 28px;border-radius:6px">
    <div style="font-size:40px;color:#fff">${esc(text("insert_caption.txt"))}</div>
    <div style="font-size:24px;color:#d0d0d0;margin-top:6px">${esc(text("insert_source.txt"))}</div></div>`;
  await page.setContent(`<html><head><meta charset="utf-8"><style>html,body{margin:0;width:1920px;height:1080px;background:transparent;
    font-family:'Noto Naskh Arabic','Noto Sans Arabic','DejaVu Sans',sans-serif}</style></head><body>${caption}</body></html>`);
  await page.screenshot({ path: path.join(OUT, "insert_caption.png"), omitBackground: true });
  await browser.close();
})().catch((err) => { console.error(err); process.exit(1); });
