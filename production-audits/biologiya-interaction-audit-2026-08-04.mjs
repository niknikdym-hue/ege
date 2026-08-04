import { chromium } from 'playwright';
import fs from 'node:fs';

const URL = 'https://eksamio.ru/ege/biologiya/demoversiya/';
const OUT = process.env.AUDIT_OUT || '/tmp/biologiya-interaction-audit';
fs.mkdirSync(OUT, { recursive: true });

const browser = await chromium.launch({
  headless: true,
  executablePath: '/usr/bin/google-chrome',
  args: ['--no-sandbox', '--disable-dev-shm-usage']
});
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
const consoleErrors = [];
const pageErrors = [];
const failedRequests = [];
page.on('console', m => { if (m.type() === 'error' && !/yandex|metrika|favicon|ResizeObserver|ERR_BLOCKED_BY_CLIENT/i.test(m.text())) consoleErrors.push(m.text()); });
page.on('pageerror', e => pageErrors.push(e.message));
page.on('requestfailed', r => { if (!/yandex|metrika|analytics|doubleclick|adfox/i.test(r.url())) failedRequests.push(`${r.method()} ${r.url()} — ${r.failure()?.errorText || 'failed'}`); });

const response = await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 90000 });
await page.waitForSelector('#eksamio-bio-demo', { timeout: 60000 });
await page.waitForFunction(() => Boolean(window.BiologyDemoTestApi && document.querySelector('#bio-start-btn')), null, { timeout: 60000 });
await page.evaluate(() => window.BiologyDemoTestApi.clear());
await page.locator('#bio-start-btn').click();
await page.waitForSelector('#bio-app.is-active', { timeout: 10000 });

function classify(text) {
  const t = text.replace(/\s+/g, ' ').trim();
  if (/установите соответствие|соответствие между/i.test(t)) return 'matching';
  if (/установите последовательность|расположите .* последовательност|последовательность .* процессов|последовательность событий/i.test(t)) return 'sequence';
  if (/выберите (?:два|три|четыре) верн|выберите верн|какие .* являются верными|какие из перечисленных .* верн/i.test(t)) return 'multiple_choice';
  if (/заполните .* таблиц|впишите .* таблиц|таблиц.*пропущ/i.test(t)) return 'table_fill';
  return 'simple_entry';
}

const tasks = [];
for (let n = 1; n <= 21; n++) {
  const button = page.locator('#bio-nav .bio-nav-btn').filter({ hasText: new RegExp(`^${n}$`) }).first();
  await button.click();
  await page.waitForFunction(num => document.querySelector('.bio-question-number')?.textContent?.trim() === `Задание ${num}`, n, { timeout: 8000 });
  await page.waitForTimeout(80);
  const data = await page.evaluate(num => {
    const root = document.querySelector('#bio-question');
    const prompt = root?.querySelector('.bio-prompt');
    const controls = [...(root?.querySelectorAll('input, select, textarea, button') || [])].map(el => ({
      tag: el.tagName.toLowerCase(),
      type: el.getAttribute('type') || '',
      id: el.id || '',
      name: el.getAttribute('name') || '',
      className: typeof el.className === 'string' ? el.className : '',
      disabled: Boolean(el.disabled),
      optionCount: el.tagName === 'SELECT' ? el.options.length : null,
      text: el.tagName === 'BUTTON' ? (el.textContent || '').trim() : ''
    }));
    return {
      number: num,
      title: root?.querySelector('.bio-question-number')?.textContent?.trim() || '',
      promptText: prompt?.innerText?.trim() || '',
      promptHtml: prompt?.innerHTML || '',
      hint: root?.querySelector('.bio-hint')?.textContent?.trim() || '',
      controls,
      genericShortInput: Boolean(root?.querySelector('#bio-answer')),
      selectCount: root?.querySelectorAll('select').length || 0,
      checkboxCount: root?.querySelectorAll('input[type="checkbox"]').length || 0,
      radioCount: root?.querySelectorAll('input[type="radio"]').length || 0,
      draggableCount: root?.querySelectorAll('[draggable="true"]').length || 0,
      answerRegionText: root?.querySelector('.bio-answer')?.innerText?.trim() || ''
    };
  }, n);
  data.expectedInteraction = classify(data.promptText);
  data.actualInteraction = data.selectCount ? 'selects' : data.checkboxCount ? 'checkboxes' : data.radioCount ? 'radios' : data.draggableCount ? 'drag_drop' : data.genericShortInput ? 'generic_text' : 'none';
  data.interactionMismatch = data.expectedInteraction !== 'simple_entry' && data.actualInteraction === 'generic_text';
  tasks.push(data);
}

const mismatches = tasks.filter(t => t.interactionMismatch);
const report = {
  url: URL,
  checkedAt: new Date().toISOString(),
  httpStatus: response?.status() || null,
  title: await page.title(),
  taskCount: tasks.length,
  mismatches: mismatches.map(t => ({ number: t.number, expectedInteraction: t.expectedInteraction, actualInteraction: t.actualInteraction, promptText: t.promptText, hint: t.hint })),
  tasks,
  consoleErrors,
  pageErrors,
  failedRequests,
  status: mismatches.length ? 'NO-GO' : 'PASS'
};
fs.writeFileSync(`${OUT}/report.json`, JSON.stringify(report, null, 2));
const lines = [
  `СТАТУС: ${report.status}`,
  `URL: ${URL}`,
  `HTTP: ${report.httpStatus}`,
  `Проверено заданий первой части: ${tasks.length}`,
  `Заданий со сложной механикой и только общим текстовым полем: ${mismatches.length}`,
  '',
  ...mismatches.map(t => `Задание ${t.number}: ${t.expectedInteraction} → ${t.actualInteraction}\n${t.promptText}\nПодсказка: ${t.hint || '—'}\n`),
  `Ошибки JS: ${consoleErrors.length}`,
  `Ошибки страницы: ${pageErrors.length}`,
  `Неудачные запросы: ${failedRequests.length}`
];
fs.writeFileSync(`${OUT}/summary.txt`, lines.join('\n'));
await page.screenshot({ path: `${OUT}/task-21.png`, fullPage: true });
console.log(lines.join('\n'));
await browser.close();
if (report.status !== 'PASS') process.exitCode = 2;
