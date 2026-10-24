// node cues.mjs > cues.json : dump the composition's sound cues and timeline constants
import { chromium } from 'playwright-core';
import { pathToFileURL } from 'node:url';
const b = await chromium.launch({
  executablePath: process.env.CHROME_PATH ?? (process.platform === 'darwin' ? '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' : '/usr/bin/google-chrome'),
});
const p = await b.newPage();
p.on('pageerror', (e) => console.error('pageerror:', e.message));
await p.goto(pathToFileURL(process.cwd() + '/' + (process.argv[2] ?? 'index.html')).href);
await p.waitForFunction(() => window.__ready === true, null, { timeout: 60000 });
console.log(JSON.stringify(await p.evaluate(() => ({ duration: window.__duration, bpm: window.__bpm, T: window.__T, cues: window.__cues, sections: window.__sections ?? [] }))));
await b.close();
