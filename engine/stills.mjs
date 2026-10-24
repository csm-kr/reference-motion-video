// node stills.mjs <composition.html> <out dir> t1 t2 ... : one PNG per time, to check layout before a full render
import { chromium } from 'playwright-core';
import { pathToFileURL } from 'node:url';
import path from 'node:path';
import fs from 'node:fs';

const [input, outDir, ...times] = process.argv.slice(2);
fs.mkdirSync(outDir, { recursive: true });
const b = await chromium.launch({
  executablePath: process.env.CHROME_PATH ?? (process.platform === 'darwin' ? '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' : '/usr/bin/google-chrome'),
});
const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
p.on('pageerror', (e) => console.error('pageerror:', e.message));
await p.goto(pathToFileURL(path.resolve(input)).href);
await p.waitForFunction(() => window.__ready === true, null, { timeout: 60000 });
for (const t of times) {
  await p.evaluate((x) => window.__seek(x), Number(t));
  await p.screenshot({ path: path.join(outDir, `t${Number(t).toFixed(2)}.png`) });
}
await b.close();
console.log(`wrote ${times.length} stills to ${outDir}`);
