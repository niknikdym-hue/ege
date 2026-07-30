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

async function visibleImageInfo(page) {
  return page.locator('img:visible').evaluateAll(images => images.map(img => ({
    alt: img.alt || '',
    srcPrefix: (img.currentSrc || img.src || '').slice(0, 40),
    naturalWidth: img.naturalWidth,
    naturalHeight: img.naturalHeight,
    clientWidth: img.clientWidth,
    clientHeight: img.clientHeight
  })).filter(item => item.naturalWidth > 0 && item.naturalHeight > 0));
}

async function auditReferences(page, name, result) {
  const openButton = page.getByRole('button', { name: /справочные материалы/i }).first();
  if (!await openButton.isVisible().catch(() => false)) {
    report.failures.push(`[${name}] Кнопка справочных материалов не найдена после старта`);
    return;
  }

  await openButton.click();
  await page.waitForTimeout(1800);
  result.referencesOpened = true;
  const dialogText = await page.locator('body').innerText();
  for (const label of ['Таблица растворимости', 'Электрохимический ряд', 'Периодическая система']) {
    if (!dialogText.toLowerCase().includes(label.toLowerCase())) {
      report.failures.push(`[${name}] В справочниках не найден раздел «${label}»`);
    }
  }

  result.referenceTabs = [];
  result.referenceImages = [];
  const tabPatterns = [/таблица растворимости/i, /электрохимический ряд/i, /периодическая система/i];
  for (let i = 0; i < tabPatterns.length; i++) {
    const tab = page.getByRole('button', { name: tabPatterns[i] }).first();
    if (await tab.isVisible().catch(() => false)) {
      result.referenceTabs.push((await tab.innerText()).trim());
      await tab.click();
      await page.waitForTimeout(1000);
      const images = await visibleImageInfo(page);
      const largeImages = images.filter(img => img.naturalWidth >= 800 && img.naturalHeight >= 500);
      result.referenceImages.push({ tab: String(tabPatterns[i]), images });
      if (!largeImages.length) report.failures.push(`[${name}] Справочник ${tabPatterns[i]} не собран в полноразмерное изображение`);
      await page.screenshot({ path: path.join(outDir, `${name}-reference-${i + 1}.png`), fullPage: true });
    } else {
      report.failures.push(`[${name}] Не найдена вкладка справочника ${tabPatterns[i]}`);
    }
  }

  const close = page.getByRole('button', { name: /закрыть|×/i }).last();
  if (await close.isVisible().catch(() => false)) {
    await close.click();
    await page.waitForTimeout(400);
  }
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
  const overflow = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    clientWidth: document.documentElement.clientWidth,
    bodyScrollWidth: document.body?.scrollWidth || 0
  }));

  const result = {
    status,
    finalUrl: page.url(),
    title,
    bodyLength: bodyText.length,
    overflow,
    buttons: (await page.getByRole('button').allTextContents()).map(x => x.trim()).filter(Boolean).slice(0, 80),
    links: (await page.getByRole('link').allTextContents()).map(x => x.trim()).filter(Boolean).slice(0, 80),
    startClicked: false,
    timerVisible: false,
    taskNavigationCount: 0,
    localStorageKeys: [],
    answerPersistence: false,
    referencesOpened: false,
    referenceTabs: [],
    referenceImages: []
  };

  await page.screenshot({ path: path.join(outDir, `${name}-initial.png`), fullPage: true });

  if (status !== 200) report.failures.push(`[${name}] HTTP status ${status}`);
  if (!/Хим/i.test(title + ' ' + bodyText.slice(0, 1000))) report.failures.push(`[${name}] Страница не выглядит как демоверсия по химии`);
  if (bodyText.length < 1000) report.failures.push(`[${name}] Слишком мало видимого содержимого: ${bodyText.length} символов`);
  if (overflow.scrollWidth - overflow.clientWidth > 5) report.failures.push(`[${name}] Горизонтальный скролл: ${overflow.scrollWidth} > ${overflow.clientWidth}`);

  const startPatterns = [/начать попытку/i, /начать демоверсию/i, /^начать$/i, /приступить/i, /продолжить попытку/i];
  let startButton = null;
  for (const re of startPatterns) {
    const candidate = page.getByRole('button', { name: re }).first();
    if (await candidate.isVisible().catch(() => false)) { startButton = candidate; break; }
  }
  if (startButton) {
    await startButton.click();
    result.startClicked = true;
    await page.waitForTimeout(2500);
  } else {
    report.failures.push(`[${name}] Кнопка старта не найдена`);
  }

  result.timerVisible = await page.getByText(/\b\d{1,2}:\d{2}:\d{2}\b/).first().isVisible().catch(() => false)
    || await page.getByText(/оставшееся время|таймер/i).first().isVisible().catch(() => false);
  if (!result.timerVisible) report.failures.push(`[${name}] Таймер не отображается после старта`);

  const numberedButtons = await page.locator('button').evaluateAll(nodes => nodes
    .map(n => (n.textContent || '').trim())
    .filter(t => /^(?:[1-9]|[12]\d|3[0-4])$/.test(t)));
  result.taskNavigationCount = new Set(numberedButtons).size;
  if (result.taskNavigationCount !== 34) report.failures.push(`[${name}] Навигация содержит ${result.taskNavigationCount} заданий вместо 34`);

  const answerInput = page.locator('input:visible:not([type="hidden"])').first();
  if (await answerInput.count()) {
    await answerInput.fill('12');
    await page.waitForTimeout(700);
    result.localStorageKeys = await page.evaluate(() => Object.keys(localStorage));
    if (!result.localStorageKeys.some(key => /eksamio_ege_khimiya/i.test(key))) {
      report.failures.push(`[${name}] Не найден ключ сохранения химии в localStorage`);
    }
    await page.reload({ waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1800);
    const restored = page.locator('input:visible:not([type="hidden"])').first();
    result.answerPersistence = await restored.inputValue().then(value => value === '12').catch(() => false);
    if (!result.answerPersistence) report.failures.push(`[${name}] Ответ не восстановился после перезагрузки`);
  } else {
    report.failures.push(`[${name}] Поле краткого ответа не найдено`);
  }

  await auditReferences(page, name, result);

  const nextButton = page.getByRole('button', { name: /следующее|далее/i }).first();
  if (await nextButton.isVisible().catch(() => false)) {
    await nextButton.click();
    await page.waitForTimeout(800);
    if (!await page.getByText(/Задание 2 из 34/i).isVisible().catch(() => false)) {
      report.failures.push(`[${name}] Переход к следующему заданию не подтверждён`);
    }
  } else {
    report.failures.push(`[${name}] Кнопка перехода к следующему заданию не найдена`);
  }

  const finalOverflow = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    clientWidth: document.documentElement.clientWidth
  }));
  if (finalOverflow.scrollWidth - finalOverflow.clientWidth > 5) {
    report.failures.push(`[${name}] Горизонтальный скролл после старта: ${finalOverflow.scrollWidth} > ${finalOverflow.clientWidth}`);
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
  if (!/favicon|ResizeObserver|Failed to load resource.*(?:yandex|analytics|adfox)/i.test(err)) report.failures.push(`Console: ${err}`);
}
for (const err of report.pageErrors) report.failures.push(`Page error: ${err}`);
for (const err of report.failedRequests) report.warnings.push(`Request: ${err}`);

report.status = report.failures.length ? 'FAIL' : 'PASS';
fs.writeFileSync(path.join(outDir, 'report.json'), JSON.stringify(report, null, 2));
console.log(JSON.stringify(report, null, 2));
if (report.failures.length) process.exit(1);
