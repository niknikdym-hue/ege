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
  viewports: {},
  variantCoverage: {},
  consoleErrors: [],
  pageErrors: [],
  failedRequests: [],
  warnings: [],
  failures: []
};

function uniquePush(arr, value) {
  if (value && !arr.includes(value)) arr.push(value);
}
function fail(message) { uniquePush(report.failures, message); }
function warn(message) { uniquePush(report.warnings, message); }

function attachDiagnostics(page, label) {
  page.on('console', msg => {
    if (msg.type() !== 'error') return;
    const text = `[${label}] ${msg.text()}`;
    if (!/favicon|ResizeObserver|mc\.yandex|yandex|analytics|adfox|ERR_BLOCKED_BY_CLIENT/i.test(text)) {
      uniquePush(report.consoleErrors, text);
    }
  });
  page.on('pageerror', err => uniquePush(report.pageErrors, `[${label}] ${err.message}`));
  page.on('requestfailed', req => {
    const url = req.url();
    if (/mc\.yandex|yandex|google-analytics|doubleclick|adfox|an\.yandex|metrika/i.test(url)) return;
    uniquePush(report.failedRequests, `[${label}] ${req.method()} ${url} — ${req.failure()?.errorText || 'failed'}`);
  });
}

async function pageOverflow(page) {
  return page.evaluate(() => {
    const doc = document.documentElement;
    const width = doc.clientWidth;
    const hasScrollableAncestor = element => {
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
      if (style.display === 'none' || style.visibility === 'hidden' || Number(style.opacity) === 0) continue;
      const rect = element.getBoundingClientRect();
      if ((rect.right > width + 3 || rect.left < -3) && !hasScrollableAncestor(element)) {
        offenders.push({
          tag: element.tagName,
          id: element.id || '',
          className: typeof element.className === 'string' ? element.className.slice(0, 120) : '',
          left: Math.round(rect.left),
          right: Math.round(rect.right),
          width: Math.round(rect.width)
        });
        if (offenders.length >= 12) break;
      }
    }
    return {
      clientWidth: width,
      scrollWidth: doc.scrollWidth,
      bodyScrollWidth: document.body?.scrollWidth || 0,
      overflowPx: Math.max(0, doc.scrollWidth - width),
      offenders
    };
  });
}

async function waitForDemo(page) {
  await page.waitForSelector('#eksamio-bio-demo', { state: 'attached', timeout: 60000 });
  await page.waitForFunction(() => {
    const start = document.querySelector('#bio-start-btn');
    const api = window.BiologyDemoTestApi;
    return Boolean(start && typeof api === 'object');
  }, { timeout: 60000 });
}

async function openFreshPage(browser, label, viewport) {
  const context = await browser.newContext({ viewport, locale: 'ru-RU' });
  const page = await context.newPage();
  attachDiagnostics(page, label);
  const response = await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 90000 });
  await waitForDemo(page);
  await page.waitForTimeout(1800);
  return { context, page, response };
}

async function clickTask(page, number) {
  const button = page.locator('#bio-nav .bio-nav-btn').filter({ hasText: new RegExp(`^${number}$`) }).first();
  if (await button.count() !== 1) throw new Error(`Не найдена кнопка задания ${number}`);
  await button.click();
  await page.waitForFunction(n => document.querySelector('.bio-question-number')?.textContent?.trim() === `Задание ${n}`, number);
  await page.waitForTimeout(90);
}

async function inspectTask(page, number, label) {
  await clickTask(page, number);
  const task = await page.evaluate(n => {
    const title = document.querySelector('.bio-question-number')?.textContent?.trim() || '';
    const variant = document.querySelector('.bio-variant')?.textContent?.trim() || '';
    const promptText = document.querySelector('.bio-prompt')?.innerText?.trim() || '';
    const images = [...document.querySelectorAll('#bio-question img')].map(img => ({
      asset: img.getAttribute('data-bio-asset') || '',
      alt: img.getAttribute('alt') || '',
      complete: img.complete,
      naturalWidth: img.naturalWidth,
      naturalHeight: img.naturalHeight,
      srcPrefix: (img.getAttribute('src') || '').slice(0, 32)
    }));
    return {
      number: n,
      title,
      variant,
      promptLength: promptText.length,
      hasShortInput: Boolean(document.querySelector('#bio-answer')),
      hasExtendedInput: Boolean(document.querySelector('#bio-ext')),
      images,
      prevDisabled: Boolean(document.querySelector('#bio-prev')?.disabled),
      nextDisabled: Boolean(document.querySelector('#bio-next')?.disabled)
    };
  }, number);

  if (task.title !== `Задание ${number}`) fail(`[${label}] Неверный заголовок задания ${number}: ${task.title}`);
  if (task.promptLength < 20) fail(`[${label}] У задания ${number} отсутствует или слишком короткое условие`);
  if (number <= 21 && !task.hasShortInput) fail(`[${label}] У задания ${number} не найдено поле краткого ответа`);
  if (number >= 22 && !task.hasExtendedInput) fail(`[${label}] У задания ${number} не найдено поле развёрнутого ответа`);
  if (number === 1 && !task.prevDisabled) fail(`[${label}] В задании 1 кнопка «Предыдущее» должна быть отключена`);
  if (number === 28 && !task.nextDisabled) fail(`[${label}] В задании 28 кнопка «Следующее» должна быть отключена`);
  for (const image of task.images) {
    if (!image.complete || image.naturalWidth < 20 || image.naturalHeight < 20) {
      fail(`[${label}] В задании ${number} не загрузилось изображение ${image.asset || image.alt || '(без подписи)'}`);
    }
  }
  const overflow = await pageOverflow(page);
  if (overflow.overflowPx > 4) {
    fail(`[${label}] Горизонтальное переполнение в задании ${number}: ${overflow.scrollWidth} > ${overflow.clientWidth}`);
  }
  return { ...task, overflow };
}

async function auditMainViewport(browser, label, viewport, fullTraversal) {
  const { context, page, response } = await openFreshPage(browser, label, viewport);
  const result = {
    viewport,
    httpStatus: response?.status() ?? null,
    finalUrl: page.url(),
    title: await page.title(),
    initialOverflow: null,
    afterStartOverflow: null,
    apiAvailable: false,
    startWorked: false,
    timerVisible: false,
    timerRuns: false,
    navCount: 0,
    answerPersistence: false,
    currentTaskPersistence: false,
    flagPersistence: false,
    tasksChecked: [],
    loadedAssets: [],
    modalWorked: false,
    resultsWorked: false,
    resultCards: [],
    reviewCount: 0,
    officialTotalPending: false,
    selfAssessmentSeparated: false,
    resetWorked: false
  };

  try {
    if (result.httpStatus !== 200) fail(`[${label}] HTTP ${result.httpStatus}`);
    if (!/биолог/i.test(result.title)) fail(`[${label}] Title не содержит указания на биологию: ${result.title}`);
    if (page.url() !== URL) warn(`[${label}] Итоговый URL отличается: ${page.url()}`);

    const initialText = (await page.locator('#eksamio-bio-demo').innerText()).trim();
    for (const expected of ['28', '235', '57', '2026']) {
      if (!initialText.includes(expected)) fail(`[${label}] На стартовом экране не найдено значение ${expected}`);
    }
    result.apiAvailable = await page.evaluate(() => typeof window.BiologyDemoTestApi === 'object');
    result.initialOverflow = await pageOverflow(page);
    if (result.initialOverflow.overflowPx > 4) fail(`[${label}] Горизонтальное переполнение до старта: ${result.initialOverflow.overflowPx}px`);
    await page.screenshot({ path: path.join(outDir, `${label}-initial.png`), fullPage: true });

    await page.locator('#bio-start-btn').click();
    await page.waitForSelector('#bio-app.is-active', { timeout: 10000 });
    result.startWorked = true;
    const timer1 = (await page.locator('#bio-timer').innerText()).trim();
    result.timerVisible = /^\d{2}:\d{2}:\d{2}$/.test(timer1);
    await page.waitForTimeout(1300);
    const timer2 = (await page.locator('#bio-timer').innerText()).trim();
    result.timerRuns = timer2 !== timer1;
    if (!result.timerVisible) fail(`[${label}] Таймер не отображается в формате ЧЧ:ММ:СС`);
    if (!result.timerRuns) fail(`[${label}] Таймер не уменьшается`);

    result.navCount = await page.locator('#bio-nav .bio-nav-btn').count();
    if (result.navCount !== 28) fail(`[${label}] Найдено ${result.navCount} кнопок заданий вместо 28`);
    result.afterStartOverflow = await pageOverflow(page);
    if (result.afterStartOverflow.overflowPx > 4) fail(`[${label}] Горизонтальное переполнение после старта: ${result.afterStartOverflow.overflowPx}px`);

    await page.locator('#bio-answer').fill('12345');
    await page.locator('#bio-flag').click();
    await page.locator('#bio-next').click();
    await page.locator('#bio-answer').fill('54321');
    await clickTask(page, 22);
    await page.locator('#bio-ext').fill('Тестовый развёрнутый ответ для проверки сохранения.');
    await page.waitForTimeout(250);
    await page.reload({ waitUntil: 'domcontentloaded', timeout: 90000 });
    await waitForDemo(page);
    const continueVisible = await page.locator('#bio-continue-btn').isVisible().catch(() => false);
    if (!continueVisible) fail(`[${label}] После перезагрузки не появилась кнопка продолжения`);
    if (continueVisible) await page.locator('#bio-continue-btn').click();
    await page.waitForSelector('#bio-app.is-active', { timeout: 10000 });
    result.currentTaskPersistence = (await page.locator('.bio-question-number').innerText()).trim() === 'Задание 22';
    result.answerPersistence = (await page.locator('#bio-ext').inputValue()) === 'Тестовый развёрнутый ответ для проверки сохранения.';
    await clickTask(page, 1);
    result.flagPersistence = await page.locator('#bio-nav .bio-nav-btn').filter({ hasText: /^1$/ }).first().evaluate(el => el.classList.contains('is-flagged'));
    const task1Value = await page.locator('#bio-answer').inputValue();
    result.answerPersistence = result.answerPersistence && task1Value === '12345';
    if (!result.currentTaskPersistence) fail(`[${label}] После перезагрузки не восстановилось открытое задание`);
    if (!result.answerPersistence) fail(`[${label}] После перезагрузки не восстановились ответы`);
    if (!result.flagPersistence) fail(`[${label}] После перезагрузки не восстановилась отметка задания`);

    const numbers = fullTraversal ? Array.from({ length: 28 }, (_, i) => i + 1) : [1, 4, 5, 6, 10, 15, 21, 22, 24, 27, 28];
    let modalTested = false;
    const assets = new Set();
    for (const number of numbers) {
      const info = await inspectTask(page, number, label);
      result.tasksChecked.push({
        number: info.number,
        variant: info.variant,
        promptLength: info.promptLength,
        imageCount: info.images.length,
        overflowPx: info.overflow.overflowPx
      });
      for (const image of info.images) if (image.asset) assets.add(image.asset);
      if (!modalTested && info.images.length) {
        const firstImage = page.locator('#bio-question img').first();
        await firstImage.click();
        await page.waitForSelector('#bio-image-modal.is-open', { timeout: 5000 });
        const modalImageLoaded = await page.locator('#bio-modal-body img').evaluate(img => img.complete && img.naturalWidth > 20);
        if (!modalImageLoaded) fail(`[${label}] Изображение в модальном окне не загрузилось`);
        await page.locator('#bio-modal-close').click();
        await page.waitForSelector('#bio-image-modal:not(.is-open)');
        modalTested = true;
        result.modalWorked = true;
      }
    }
    result.loadedAssets = [...assets].sort();
    await page.screenshot({ path: path.join(outDir, `${label}-after-start.png`), fullPage: true });

    await clickTask(page, 22);
    await page.evaluate(() => window.BiologyDemoTestApi.finishNow());
    await page.waitForSelector('#bio-results.is-active', { timeout: 10000 });
    result.resultsWorked = true;
    result.resultCards = await page.locator('.bio-score-grid .bio-score').allInnerTexts();
    result.reviewCount = await page.locator('.bio-review-card').count();
    const resultsText = (await page.locator('#bio-results').innerText()).replace(/\s+/g, ' ');
    result.officialTotalPending = /—\s*\/\s*57/.test(resultsText) && /официальный первичный балл определяется после экспертной проверки/i.test(resultsText);
    result.selfAssessmentSeparated = /учебная самооценка второй части/i.test(resultsText)
      && /не прибавляется к результату первой части/i.test(resultsText)
      && !/\b\d+\s*\/\s*57\b/.test(resultsText);
    if (result.reviewCount !== 28) fail(`[${label}] В результатах ${result.reviewCount} карточек вместо 28`);
    if (!result.officialTotalPending) fail(`[${label}] Не показано, что официальный балл из 57 ожидает экспертной проверки`);
    if (!result.selfAssessmentSeparated) fail(`[${label}] Учебная самооценка второй части не отделена от официального результата`);

    const emptyExtendedDisabled = await page.locator('[data-self-task="23"]').first().isDisabled().catch(() => false);
    if (!emptyExtendedDisabled) fail(`[${label}] Самооценка пустого развёрнутого ответа должна быть отключена`);
    const answeredExtendedEnabled = await page.locator('[data-self-task="22"]').first().isEnabled().catch(() => false);
    if (!answeredExtendedEnabled) fail(`[${label}] Самооценка введённого развёрнутого ответа недоступна`);
    if (answeredExtendedEnabled) {
      const before = (await page.locator('#bio-self-total').innerText()).trim();
      await page.locator('[data-self-task="22"]').first().check();
      const after = (await page.locator('#bio-self-total').innerText()).trim();
      if (before === after) fail(`[${label}] Сумма учебной самооценки не обновилась после выбора критерия`);
    }
    await page.screenshot({ path: path.join(outDir, `${label}-results.png`), fullPage: true });

    await page.locator('#bio-retry').click();
    await page.waitForSelector('#bio-start-btn', { state: 'visible', timeout: 5000 });
    const storageValue = await page.evaluate(() => localStorage.getItem('eksamio_ege_biologiya_demo_2026_v1'));
    result.resetWorked = storageValue === null;
    if (!result.resetWorked) fail(`[${label}] Новая попытка не очистила сохранённое состояние`);
  } catch (error) {
    fail(`[${label}] ${error.stack || error.message}`);
    try { await page.screenshot({ path: path.join(outDir, `${label}-failure.png`), fullPage: true }); } catch {}
  } finally {
    report.viewports[label] = result;
    await context.close();
  }
}

async function auditVariantCombo(browser, label, forced, tasks) {
  const { context, page, response } = await openFreshPage(browser, label, { width: 1280, height: 900 });
  const result = { forced, httpStatus: response?.status() ?? null, tasks: [], assets: [] };
  try {
    await page.evaluate(v => window.BiologyDemoTestApi.startWithVariants(v), forced);
    await page.waitForSelector('#bio-app.is-active', { timeout: 10000 });
    const assets = new Set();
    for (const number of tasks) {
      const info = await inspectTask(page, number, label);
      result.tasks.push({ number, variant: info.variant, promptLength: info.promptLength, imageCount: info.images.length });
      for (const image of info.images) if (image.asset) assets.add(image.asset);
    }
    result.assets = [...assets].sort();
    await page.screenshot({ path: path.join(outDir, `${label}.png`), fullPage: true });
  } catch (error) {
    fail(`[${label}] ${error.stack || error.message}`);
  } finally {
    report.variantCoverage[label] = result;
    await context.close();
  }
}

const browser = await chromium.launch({ headless: true });
try {
  await auditMainViewport(browser, 'desktop-1440', { width: 1440, height: 1000 }, true);
  await auditMainViewport(browser, 'tablet-768', { width: 768, height: 1024 }, false);
  await auditMainViewport(browser, 'mobile-390', { width: 390, height: 844 }, false);
  await auditMainViewport(browser, 'mobile-360', { width: 360, height: 800 }, false);
  await auditMainViewport(browser, 'mobile-320', { width: 320, height: 700 }, false);

  await auditVariantCombo(browser, 'variants-all-1', { '4': 1, '56': 1, '24': 1, '27': 1 }, [4, 5, 6, 24, 27]);
  await auditVariantCombo(browser, 'variants-all-2', { '4': 2, '56': 2, '24': 2, '27': 2 }, [4, 5, 6, 24, 27]);
  await auditVariantCombo(browser, 'variant-27-3', { '4': 1, '56': 1, '24': 1, '27': 3 }, [27]);
  await auditVariantCombo(browser, 'variant-27-4', { '4': 1, '56': 1, '24': 1, '27': 4 }, [27]);
} finally {
  await browser.close();
}

for (const error of report.consoleErrors) fail(`Console: ${error}`);
for (const error of report.pageErrors) fail(`Page error: ${error}`);
for (const request of report.failedRequests) warn(`Request: ${request}`);

const allAssets = new Set();
for (const viewport of Object.values(report.viewports)) for (const asset of viewport.loadedAssets || []) allAssets.add(asset);
for (const combo of Object.values(report.variantCoverage)) for (const asset of combo.assets || []) allAssets.add(asset);
report.loadedAssets = [...allAssets].sort();
if (report.loadedAssets.length !== 11) {
  fail(`Во всех вариантах найдено ${report.loadedAssets.length} уникальных изображений вместо 11: ${report.loadedAssets.join(', ')}`);
}

const expectedVariants = {
  'variants-all-1': { 4: 'Вариант 1', 5: 'Вариант 1', 6: 'Вариант 1', 24: 'Вариант 1', 27: 'Вариант 1' },
  'variants-all-2': { 4: 'Вариант 2', 5: 'Вариант 2', 6: 'Вариант 2', 24: 'Вариант 2', 27: 'Вариант 2' },
  'variant-27-3': { 27: 'Вариант 3' },
  'variant-27-4': { 27: 'Вариант 4' }
};
for (const [label, expected] of Object.entries(expectedVariants)) {
  const actual = Object.fromEntries((report.variantCoverage[label]?.tasks || []).map(task => [task.number, task.variant]));
  for (const [number, variant] of Object.entries(expected)) {
    if (actual[number] !== variant) fail(`[${label}] Для задания ${number} ожидалась метка «${variant}», получено «${actual[number] || 'нет'}»`);
  }
}

report.status = report.failures.length ? 'FAIL' : 'PASS';
fs.writeFileSync(path.join(outDir, 'report.json'), JSON.stringify(report, null, 2));
const summary = [
  `BIOLOGY LIVE PRODUCTION AUDIT`,
  `URL: ${URL}`,
  `CHECKED_AT: ${report.checkedAt}`,
  `STATUS: ${report.status}`,
  `VIEWPORTS: ${Object.keys(report.viewports).join(', ')}`,
  `UNIQUE_ASSETS: ${report.loadedAssets.length}`,
  `FAILURES: ${report.failures.length}`,
  ...report.failures.map(x => `- ${x}`),
  `WARNINGS: ${report.warnings.length}`,
  ...report.warnings.map(x => `- ${x}`)
].join('\n');
fs.writeFileSync(path.join(outDir, 'summary.txt'), summary);
console.log(JSON.stringify(report, null, 2));
if (report.failures.length) process.exit(1);
