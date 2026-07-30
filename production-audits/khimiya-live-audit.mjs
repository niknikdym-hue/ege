import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';

const URL = 'https://eksamio.ru/ege/khimiya/demoversiya/';
const outDir = process.env.AUDIT_OUT || '/tmp/khimiya-live-audit';
fs.mkdirSync(outDir, { recursive: true });

const report = {
  url: URL,
  checkedAt: new Date().toISOString(),
  desktop: {},
  mobile: {},
  consoleErrors: [],
  pageErrors: [],
  failedRequests: [],
  warnings: [],
  failures: []
};

function pushUnique(arr, value) {
  if (value && !arr.includes(value)) arr.push(value);
}

async function auditViewport(browser, name, viewport) {
  const context = await browser.newContext({ viewport, locale: 'ru-RU' });
  const page = await context.newPage();

  page.on('console', msg => {
    if (msg.type() === 'error') pushUnique(report.consoleErrors, `[${name}] ${msg.text()}`);
  });
  page.on('pageerror', err => pushUnique(report.pageErrors, `[${name}] ${err.message}`));
  page.on('requestfailed', req => {
    const failure = req.failure();
    const value = `[${name}] ${req.method()} ${req.url()} — ${failure?.errorText || 'failed'}`;
    if (!/mc\.yandex|yandex|google-analytics|doubleclick|adfox|an\.yandex/i.test(req.url())) {
      pushUnique(report.failedRequests, value);
    }
  });

  const response = await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 90000 });
  await page.waitForTimeout(5000);

  const status = response?.status() ?? null;
  const title = await page.title();
  const bodyText = (await page.locator('body').innerText()).trim();
  const bodyLength = bodyText.length;
  const finalUrl = page.url();
  const overflow = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    clientWidth: document.documentElement.clientWidth,
    bodyScrollWidth: document.body?.scrollWidth || 0
  }));

  const visibleTexts = await page.getByRole('button').allTextContents();
  const links = await page.getByRole('link').allTextContents();
  const inputs = await page.locator('input').count();
  const textareas = await page.locator('textarea').count();
  const scripts = await page.locator('script').count();

  const result = {
    status,
    finalUrl,
    title,
    bodyLength,
    overflow,
    buttons: visibleTexts.map(x => x.trim()).filter(Boolean).slice(0, 80),
    links: links.map(x => x.trim()).filter(Boolean).slice(0, 80),
    inputs,
    textareas,
    scripts,
    startClicked: false,
    timerVisible: false,
    taskNavigationCount: 0,
    referenceControls: [],
    localStorageKeys: []
  };

  await page.screenshot({ path: path.join(outDir, `${name}-initial.png`), fullPage: true });

  if (status !== 200) report.failures.push(`[${name}] HTTP status ${status}`);
  if (!/Хим/i.test(title + ' ' + bodyText.slice(0, 1000))) report.failures.push(`[${name}] Страница не выглядит как демоверсия по химии`);
  if (bodyLength < 1000) report.failures.push(`[${name}] Слишком мало видимого содержимого: ${bodyLength} символов`);
  if (overflow.scrollWidth - overflow.clientWidth > 5) report.failures.push(`[${name}] Горизонтальный скролл: ${overflow.scrollWidth} > ${overflow.clientWidth}`);

  const startCandidates = [
    /начать попытку/i,
    /начать демоверсию/i,
    /^начать$/i,
    /приступить/i,
    /продолжить попытку/i
  ];
  let startButton = null;
  for (const re of startCandidates) {
    const candidate = page.getByRole('button', { name: re }).first();
    if (await candidate.count()) {
      if (await candidate.isVisible().catch(() => false)) { startButton = candidate; break; }
    }
  }

  if (startButton) {
    await startButton.click();
    result.startClicked = true;
    await page.waitForTimeout(2500);
  } else {
    report.warnings.push(`[${name}] Кнопка старта не найдена; возможно, попытка уже открыта`);
  }

  result.timerVisible = await page.getByText(/\b\d{1,2}:\d{2}:\d{2}\b/).first().isVisible().catch(() => false)
    || await page.getByText(/оставшееся время|таймер/i).first().isVisible().catch(() => false);

  const numberedButtons = await page.locator('button').evaluateAll(nodes => nodes
    .map(n => (n.textContent || '').trim())
    .filter(t => /^(?:[1-9]|[12]\d|3[0-4])$/.test(t)));
  result.taskNavigationCount = new Set(numberedButtons).size;

  const referenceRegexes = [/справоч/i, /таблиц.*раствор/i, /периодическ/i, /электрохим/i];
  for (const re of referenceRegexes) {
    const matches = page.getByText(re);
    const count = await matches.count();
    for (let i = 0; i < Math.min(count, 5); i++) {
      const text = (await matches.nth(i).innerText().catch(() => '')).trim();
      if (text) pushUnique(result.referenceControls, text);
    }
  }

  result.localStorageKeys = await page.evaluate(() => Object.keys(localStorage));

  if (!result.timerVisible) report.warnings.push(`[${name}] Таймер не подтверждён автоматически`);
  if (result.taskNavigationCount < 30) report.warnings.push(`[${name}] Найдено только ${result.taskNavigationCount} кнопок навигации заданий`);
  if (result.referenceControls.length === 0) report.warnings.push(`[${name}] Не найдены видимые элементы справочных материалов`);

  const nextButton = page.getByRole('button', { name: /следующее|далее/i }).first();
  if (await nextButton.isVisible().catch(() => false)) {
    await nextButton.click();
    await page.waitForTimeout(800);
    await page.reload({ waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1800);
    const afterReloadText = (await page.locator('body').innerText()).slice(0, 3000);
    if (!/задание|вопрос/i.test(afterReloadText)) report.warnings.push(`[${name}] После перехода и перезагрузки не подтверждено восстановление попытки`);
  }

  await page.screenshot({ path: path.join(outDir, `${name}-after-start.png`), fullPage: true });
  await context.close();
  return result;
}

const browser = await chromium.launch({ headless: true });
try {
  report.desktop = await auditViewport(browser, 'desktop-1440', { width: 1440, height: 1000 });
  report.mobile = await auditViewport(browser, 'mobile-360', { width: 360, height: 800 });
} finally {
  await browser.close();
}

for (const err of report.consoleErrors) {
  if (!/favicon|ResizeObserver|Failed to load resource.*(?:yandex|analytics|adfox)/i.test(err)) {
    report.failures.push(`Console: ${err}`);
  }
}
for (const err of report.pageErrors) report.failures.push(`Page error: ${err}`);
for (const err of report.failedRequests) report.warnings.push(`Request: ${err}`);

report.status = report.failures.length ? 'FAIL' : 'PASS';
fs.writeFileSync(path.join(outDir, 'report.json'), JSON.stringify(report, null, 2));
console.log(JSON.stringify(report, null, 2));
if (report.failures.length) process.exit(1);
