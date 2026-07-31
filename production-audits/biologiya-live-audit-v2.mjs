import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';

const URL = 'https://eksamio.ru/ege/biologiya/demoversiya/';
const outDir = process.env.AUDIT_OUT || '/tmp/biologiya-live-audit';
fs.mkdirSync(outDir, { recursive: true });

const report = {
  url: URL,
  checkedAt: new Date().toISOString(),
  status: 'PENDING',
  httpStatus: null,
  title: '',
  finalUrl: '',
  viewports: {},
  variants: {},
  loadedAssets: [],
  consoleErrors: [],
  pageErrors: [],
  failedRequests: [],
  warnings: [],
  failures: []
};

const addUnique = (arr, value) => { if (value && !arr.includes(value)) arr.push(value); };
const fail = value => addUnique(report.failures, value);
const warn = value => addUnique(report.warnings, value);

function attachDiagnostics(page) {
  page.on('console', msg => {
    if (msg.type() !== 'error') return;
    const text = msg.text();
    if (!/favicon|ResizeObserver|mc\.yandex|yandex|analytics|adfox|ERR_BLOCKED_BY_CLIENT/i.test(text)) {
      addUnique(report.consoleErrors, text);
    }
  });
  page.on('pageerror', err => addUnique(report.pageErrors, err.message));
  page.on('requestfailed', req => {
    const url = req.url();
    if (/mc\.yandex|yandex|google-analytics|doubleclick|adfox|an\.yandex|metrika/i.test(url)) return;
    addUnique(report.failedRequests, `${req.method()} ${url} — ${req.failure()?.errorText || 'failed'}`);
  });
}

async function waitForDemo(page) {
  await page.waitForSelector('#eksamio-bio-demo', { state: 'attached', timeout: 60000 });
  await page.waitForFunction(() => Boolean(document.querySelector('#bio-start-btn') && window.BiologyDemoTestApi), null, { timeout: 60000 });
}

async function getOverflow(page) {
  return page.evaluate(() => {
    const doc = document.documentElement;
    const viewportWidth = doc.clientWidth;
    const hasInternalScroll = element => {
      let node = element.parentElement;
      while (node && node !== document.body && node !== doc) {
        const style = getComputedStyle(node);
        if (/(auto|scroll)/.test(style.overflowX) && node.scrollWidth > node.clientWidth + 2) return true;
        node = node.parentElement;
      }
      return false;
    };
    const offenders = [];
    for (const element of document.querySelectorAll('body *')) {
      const style = getComputedStyle(element);
      if (style.display === 'none' || style.visibility === 'hidden') continue;
      const rect = element.getBoundingClientRect();
      if ((rect.right > viewportWidth + 3 || rect.left < -3) && !hasInternalScroll(element)) {
        offenders.push({
          tag: element.tagName,
          id: element.id || '',
          className: typeof element.className === 'string' ? element.className.slice(0, 100) : '',
          left: Math.round(rect.left),
          right: Math.round(rect.right),
          width: Math.round(rect.width)
        });
        if (offenders.length >= 10) break;
      }
    }
    return {
      clientWidth: viewportWidth,
      scrollWidth: doc.scrollWidth,
      overflowPx: Math.max(0, doc.scrollWidth - viewportWidth),
      offenders
    };
  });
}

async function clearAttempt(page) {
  await page.evaluate(() => window.BiologyDemoTestApi.clear());
  await page.waitForSelector('#bio-start-btn', { state: 'visible', timeout: 5000 });
}

async function clickTask(page, number) {
  const button = page.locator('#bio-nav .bio-nav-btn').filter({ hasText: new RegExp(`^${number}$`) }).first();
  if (await button.count() !== 1) throw new Error(`Не найдена кнопка задания ${number}`);
  await button.click();
  await page.waitForFunction(n => document.querySelector('.bio-question-number')?.textContent?.trim() === `Задание ${n}`, number, { timeout: 8000 });
  await page.waitForTimeout(70);
}

async function inspectTask(page, number, label) {
  await clickTask(page, number);
  const task = await page.evaluate(n => {
    const prompt = document.querySelector('.bio-prompt')?.innerText?.trim() || '';
    const images = [...document.querySelectorAll('#bio-question img')].map(img => ({
      asset: img.getAttribute('data-bio-asset') || '',
      alt: img.alt || '',
      complete: img.complete,
      naturalWidth: img.naturalWidth,
      naturalHeight: img.naturalHeight
    }));
    return {
      number: n,
      title: document.querySelector('.bio-question-number')?.textContent?.trim() || '',
      variant: document.querySelector('.bio-variant')?.textContent?.trim() || '',
      promptLength: prompt.length,
      shortInput: Boolean(document.querySelector('#bio-answer')),
      extendedInput: Boolean(document.querySelector('#bio-ext')),
      prevDisabled: Boolean(document.querySelector('#bio-prev')?.disabled),
      nextDisabled: Boolean(document.querySelector('#bio-next')?.disabled),
      images
    };
  }, number);

  if (task.title !== `Задание ${number}`) fail(`[${label}] Неверный заголовок задания ${number}: «${task.title}»`);
  if (task.promptLength < 20) fail(`[${label}] У задания ${number} отсутствует полноценное условие`);
  if (number <= 21 && !task.shortInput) fail(`[${label}] У задания ${number} нет поля краткого ответа`);
  if (number >= 22 && !task.extendedInput) fail(`[${label}] У задания ${number} нет поля развёрнутого ответа`);
  if (number === 1 && !task.prevDisabled) fail(`[${label}] В задании 1 активна кнопка «Предыдущее»`);
  if (number === 28 && !task.nextDisabled) fail(`[${label}] В задании 28 активна кнопка «Следующее»`);
  for (const image of task.images) {
    if (!image.complete || image.naturalWidth < 20 || image.naturalHeight < 20) {
      fail(`[${label}] В задании ${number} не загрузилось изображение ${image.asset || image.alt || '(без подписи)'}`);
    }
  }
  const overflow = await getOverflow(page);
  if (overflow.overflowPx > 4) fail(`[${label}] Горизонтальный выход в задании ${number}: ${overflow.overflowPx}px`);
  return { ...task, overflow };
}

async function startNormally(page) {
  await page.locator('#bio-start-btn').click();
  await page.waitForSelector('#bio-app.is-active', { timeout: 8000 });
}

async function checkTimerAndNav(page, label, result) {
  const before = (await page.locator('#bio-timer').innerText()).trim();
  result.timerVisible = /^\d{2}:\d{2}:\d{2}$/.test(before);
  await page.waitForTimeout(1250);
  const after = (await page.locator('#bio-timer').innerText()).trim();
  result.timerRuns = before !== after;
  result.navCount = await page.locator('#bio-nav .bio-nav-btn').count();
  if (!result.timerVisible) fail(`[${label}] Таймер имеет неверный формат`);
  if (!result.timerRuns) fail(`[${label}] Таймер не уменьшается`);
  if (result.navCount !== 28) fail(`[${label}] В навигации ${result.navCount} заданий вместо 28`);
}

async function testImageModal(page, label, result) {
  const firstImage = page.locator('#bio-question img').first();
  if (!await firstImage.count()) return;
  await firstImage.click();
  await page.waitForSelector('#bio-image-modal.is-open', { state: 'visible', timeout: 5000 });
  const loaded = await page.locator('#bio-modal-body img').evaluate(img => img.complete && img.naturalWidth > 20);
  if (!loaded) fail(`[${label}] Увеличенная версия рисунка не загрузилась`);
  await page.locator('#bio-modal-close').click();
  await page.waitForFunction(() => !document.querySelector('#bio-image-modal')?.classList.contains('is-open'), null, { timeout: 5000 });
  result.imageModal = true;
}

async function testPersistence(page, label, result) {
  await clickTask(page, 1);
  await page.locator('#bio-answer').fill('12345');
  await page.locator('#bio-flag').click();
  await clickTask(page, 2);
  await page.locator('#bio-answer').fill('54321');
  await clickTask(page, 22);
  await page.locator('#bio-ext').fill('Тестовый развёрнутый ответ для проверки сохранения.');
  await page.waitForTimeout(220);
  await page.reload({ waitUntil: 'domcontentloaded', timeout: 90000 });
  await waitForDemo(page);
  result.continueVisible = await page.locator('#bio-continue-btn').isVisible().catch(() => false);
  if (!result.continueVisible) {
    fail(`[${label}] После перезагрузки нет кнопки продолжения`);
    return;
  }
  await page.locator('#bio-continue-btn').click();
  await page.waitForSelector('#bio-app.is-active', { timeout: 8000 });
  result.currentTaskRestored = (await page.locator('.bio-question-number').innerText()).trim() === 'Задание 22';
  result.extendedRestored = (await page.locator('#bio-ext').inputValue()) === 'Тестовый развёрнутый ответ для проверки сохранения.';
  await clickTask(page, 1);
  result.shortRestored = (await page.locator('#bio-answer').inputValue()) === '12345';
  result.flagRestored = await page.locator('#bio-nav .bio-nav-btn').filter({ hasText: /^1$/ }).first().evaluate(el => el.classList.contains('is-flagged'));
  if (!result.currentTaskRestored) fail(`[${label}] Не восстановилось открытое задание`);
  if (!result.extendedRestored || !result.shortRestored) fail(`[${label}] Не восстановились введённые ответы`);
  if (!result.flagRestored) fail(`[${label}] Не восстановилась отметка задания`);
}

async function testResults(page, label, result) {
  await clickTask(page, 22);
  if (!await page.locator('#bio-ext').inputValue()) await page.locator('#bio-ext').fill('Ответ для проверки критериев.');
  await page.evaluate(() => window.BiologyDemoTestApi.finishNow());
  await page.waitForSelector('#bio-results.is-active', { timeout: 8000 });
  const text = (await page.locator('#bio-results').innerText()).replace(/\s+/g, ' ');
  result.reviewCount = await page.locator('.bio-review-card').count();
  result.scoreCards = await page.locator('.bio-score-grid .bio-score').allInnerTexts();
  result.officialPending = /—\s*\/\s*57/.test(text) && /официальный первичный балл определяется после экспертной проверки/i.test(text);
  result.selfSeparated = /учебная самооценка второй части/i.test(text)
    && /не прибавляется к результату первой части/i.test(text)
    && !/\b\d+\s*\/\s*57\b/.test(text);
  if (result.reviewCount !== 28) fail(`[${label}] В результатах ${result.reviewCount} карточек вместо 28`);
  if (!result.officialPending) fail(`[${label}] Не указано ожидание экспертной проверки для официального балла из 57`);
  if (!result.selfSeparated) fail(`[${label}] Самооценка второй части смешана с официальным результатом`);

  const emptyDisabled = await page.locator('[data-self-task="23"]').first().isDisabled().catch(() => false);
  const answeredEnabled = await page.locator('[data-self-task="22"]').first().isEnabled().catch(() => false);
  if (!emptyDisabled) fail(`[${label}] Критерии пустого задания 23 должны быть отключены`);
  if (!answeredEnabled) fail(`[${label}] Критерии заполненного задания 22 недоступны`);
  if (answeredEnabled) {
    const before = (await page.locator('#bio-self-total').innerText()).trim();
    await page.locator('[data-self-task="22"]').first().check();
    const after = (await page.locator('#bio-self-total').innerText()).trim();
    if (before === after) fail(`[${label}] Учебная самооценка не обновляется`);
  }
  await page.screenshot({ path: path.join(outDir, `${label}-results.png`), fullPage: true });
  await page.locator('#bio-retry').click();
  await page.waitForSelector('#bio-start-btn', { state: 'visible', timeout: 5000 });
  result.resetClearedStorage = await page.evaluate(() => localStorage.getItem('eksamio_ege_biologiya_demo_2026_v1') === null);
  if (!result.resetClearedStorage) fail(`[${label}] Новая попытка не очистила localStorage`);
}

async function auditViewport(page, label, viewport, tasks, options = {}) {
  await page.setViewportSize(viewport);
  await clearAttempt(page);
  const result = {
    viewport,
    initialOverflow: await getOverflow(page),
    started: false,
    timerVisible: false,
    timerRuns: false,
    navCount: 0,
    taskChecks: [],
    assets: [],
    imageModal: false
  };
  if (result.initialOverflow.overflowPx > 4) fail(`[${label}] Горизонтальный выход до старта: ${result.initialOverflow.overflowPx}px`);
  await page.screenshot({ path: path.join(outDir, `${label}-initial.png`), fullPage: true });
  try {
    await startNormally(page);
    result.started = true;
    await checkTimerAndNav(page, label, result);
    if (options.persistence) await testPersistence(page, label, result);
    const assets = new Set();
    let modalDone = false;
    for (const number of tasks) {
      const info = await inspectTask(page, number, label);
      result.taskChecks.push({ number, variant: info.variant, promptLength: info.promptLength, imageCount: info.images.length, overflowPx: info.overflow.overflowPx });
      for (const image of info.images) if (image.asset) assets.add(image.asset);
      if (!modalDone && info.images.length) {
        await testImageModal(page, label, result);
        modalDone = true;
      }
    }
    result.assets = [...assets].sort();
    await page.screenshot({ path: path.join(outDir, `${label}-after-start.png`), fullPage: true });
    if (options.results) await testResults(page, label, result);
  } catch (error) {
    fail(`[${label}] ${error.stack || error.message}`);
    try { await page.screenshot({ path: path.join(outDir, `${label}-failure.png`), fullPage: true }); } catch {}
  }
  report.viewports[label] = result;
}

async function auditVariant(page, label, forced, tasks) {
  await page.setViewportSize({ width: 1280, height: 900 });
  await clearAttempt(page);
  const result = { forced, tasks: [], assets: [] };
  try {
    await page.evaluate(v => window.BiologyDemoTestApi.startWithVariants(v), forced);
    await page.waitForSelector('#bio-app.is-active', { timeout: 8000 });
    const assets = new Set();
    for (const number of tasks) {
      const info = await inspectTask(page, number, label);
      result.tasks.push({ number, variant: info.variant, promptLength: info.promptLength, imageCount: info.images.length });
      for (const image of info.images) if (image.asset) assets.add(image.asset);
    }
    result.assets = [...assets].sort();
  } catch (error) {
    fail(`[${label}] ${error.stack || error.message}`);
  }
  report.variants[label] = result;
}

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, locale: 'ru-RU' });
const page = await context.newPage();
attachDiagnostics(page);
try {
  const response = await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 90000 });
  report.httpStatus = response?.status() ?? null;
  report.finalUrl = page.url();
  report.title = await page.title();
  await waitForDemo(page);
  await page.waitForTimeout(1800);
  if (report.httpStatus !== 200) fail(`HTTP ${report.httpStatus}`);
  if (!/биолог/i.test(report.title)) fail(`Title не содержит биологию: ${report.title}`);
  const startText = (await page.locator('#eksamio-bio-demo').innerText()).trim();
  for (const expected of ['28', '235', '57', '2026']) if (!startText.includes(expected)) fail(`На стартовом экране нет значения ${expected}`);

  await auditViewport(page, 'desktop-1440', { width: 1440, height: 1000 }, Array.from({ length: 28 }, (_, i) => i + 1), { persistence: true, results: true });
  await auditViewport(page, 'tablet-768', { width: 768, height: 1024 }, [1, 4, 5, 6, 10, 15, 21, 22, 24, 27, 28]);
  await auditViewport(page, 'mobile-390', { width: 390, height: 844 }, [1, 4, 5, 6, 10, 15, 21, 22, 24, 27, 28]);
  await auditViewport(page, 'mobile-360', { width: 360, height: 800 }, [1, 4, 5, 6, 10, 15, 21, 22, 24, 27, 28]);
  await auditViewport(page, 'mobile-320', { width: 320, height: 700 }, [1, 4, 5, 6, 10, 15, 21, 22, 24, 27, 28], { results: true });

  await auditVariant(page, 'variants-all-1', { '4': 1, '56': 1, '24': 1, '27': 1 }, [4, 5, 6, 24, 27]);
  await auditVariant(page, 'variants-all-2', { '4': 2, '56': 2, '24': 2, '27': 2 }, [4, 5, 6, 24, 27]);
  await auditVariant(page, 'variant-27-3', { '4': 1, '56': 1, '24': 1, '27': 3 }, [27]);
  await auditVariant(page, 'variant-27-4', { '4': 1, '56': 1, '24': 1, '27': 4 }, [27]);
} catch (error) {
  fail(`Критический сбой аудита: ${error.stack || error.message}`);
  try { await page.screenshot({ path: path.join(outDir, 'critical-failure.png'), fullPage: true }); } catch {}
} finally {
  await context.close();
  await browser.close();
}

for (const error of report.consoleErrors) fail(`Console: ${error}`);
for (const error of report.pageErrors) fail(`Page error: ${error}`);
for (const request of report.failedRequests) warn(`Request: ${request}`);

const assets = new Set();
for (const result of Object.values(report.viewports)) for (const asset of result.assets || []) assets.add(asset);
for (const result of Object.values(report.variants)) for (const asset of result.assets || []) assets.add(asset);
report.loadedAssets = [...assets].sort();
if (report.loadedAssets.length !== 11) fail(`Найдено ${report.loadedAssets.length} уникальных рисунков вместо 11: ${report.loadedAssets.join(', ')}`);

const expectedVariants = {
  'variants-all-1': { 4: 'Вариант 1', 5: 'Вариант 1', 6: 'Вариант 1', 24: 'Вариант 1', 27: 'Вариант 1' },
  'variants-all-2': { 4: 'Вариант 2', 5: 'Вариант 2', 6: 'Вариант 2', 24: 'Вариант 2', 27: 'Вариант 2' },
  'variant-27-3': { 27: 'Вариант 3' },
  'variant-27-4': { 27: 'Вариант 4' }
};
for (const [label, expected] of Object.entries(expectedVariants)) {
  const actual = Object.fromEntries((report.variants[label]?.tasks || []).map(task => [task.number, task.variant]));
  for (const [number, variant] of Object.entries(expected)) {
    if (actual[number] !== variant) fail(`[${label}] Задание ${number}: ожидалось «${variant}», получено «${actual[number] || 'нет'}»`);
  }
}

report.status = report.failures.length ? 'FAIL' : 'PASS';
fs.writeFileSync(path.join(outDir, 'report.json'), JSON.stringify(report, null, 2));
fs.writeFileSync(path.join(outDir, 'summary.txt'), [
  'BIOLOGY LIVE PRODUCTION AUDIT',
  `URL: ${URL}`,
  `CHECKED_AT: ${report.checkedAt}`,
  `STATUS: ${report.status}`,
  `HTTP_STATUS: ${report.httpStatus}`,
  `VIEWPORTS: ${Object.keys(report.viewports).join(', ')}`,
  `UNIQUE_ASSETS: ${report.loadedAssets.length}`,
  `FAILURES: ${report.failures.length}`,
  ...report.failures.map(x => `- ${x}`),
  `WARNINGS: ${report.warnings.length}`,
  ...report.warnings.map(x => `- ${x}`)
].join('\n'));
console.log(JSON.stringify(report, null, 2));
if (report.failures.length) process.exit(1);
