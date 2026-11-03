// Render the logo overlay: a transparent 1920x1080 PNG laid over every shot.
// Placeholder: draws nothing yet. Run: NODE_PATH=<dir with playwright> node logos.js <out_dir>
const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const OUT = process.argv[2] || path.join(__dirname, "out");

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  await page.setContent(`<html><head><meta charset="utf-8"><style>html,body{margin:0;background:transparent}</style></head><body></body></html>`);
  await page.screenshot({ path: path.join(OUT, "logos.png"), omitBackground: true });
  await browser.close();
})().catch((err) => { console.error(err); process.exit(1); });
