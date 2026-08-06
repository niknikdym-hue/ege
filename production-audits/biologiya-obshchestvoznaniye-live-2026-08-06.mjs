import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';

const outDir = process.env.AUDIT_OUT || '/tmp/bio-soc-live-audit';
fs.mkdirSync(outDir, { recursive: true });
const report = { checkedAt: new Date().toISOString(), status: 'PENDING', biology: {}, social: {}, failures: [] };
const fail = (scope, message) => { report.failures.push(`[${scope}] ${message}`); };

function diagnostics(page, bag) {
  page.on('pageerror', e => bag.pageErrors.push(String(e)));
  page.on('console', m => { if (m.type() === 'error' && !/yandex|metrika|favicon|analytics/i.test(m.text())) bag.consoleErrors.push(m.text()); });
  page.on('requestfailed', r => { if (!/yandex|metrika|analytics|favicon/i.test(r.url())) bag.failedRequests.push(`${r.method()} ${r.url()} ${r.failure()?.errorText || ''}`); });
}
async function overflow(page) { return page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth); }
async function loadedImages(page, selector) { return page.locator(selector).evaluateAll(imgs => imgs.every(img => img.complete && img.naturalWidth > 20 && img.naturalHeight > 20)); }

async function auditBiology(browser) {
  const scope = 'Биология';
  const r = report.biology = { url: 'https://eksamio.ru/ege/biologiya/demoversiya/', status: 'PENDING', pageErrors: [], consoleErrors: [], failedRequests: [], checks: [] };
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
  const page = await context.newPage(); diagnostics(page, r);
  try {
    const response = await page.goto(r.url, { waitUntil: 'domcontentloaded', timeout: 90000 });
    r.httpStatus = response?.status() || null;
    if (r.httpStatus !== 200) fail(scope, `HTTP ${r.httpStatus}`);
    await page.waitForSelector('#eksamio-bio-demo', { timeout: 60000 });
    await page.waitForFunction(() => !!window.BiologyDemoTestApi, null, { timeout: 60000 });
    await page.evaluate(() => window.BiologyDemoTestApi.clear());
    await page.evaluate(() => window.BiologyDemoTestApi.startWithVariants({ '4': 1, '56': 1, '24': 1, '27': 1 }));
    await page.waitForSelector('#bio-app.is-active', { timeout: 10000 });
    r.navCount = await page.locator('#bio-nav .bio-nav-btn').count();
    if (r.navCount !== 28) fail(scope, `В навигации ${r.navCount} заданий вместо 28`);
    r.storageKeys = await page.evaluate(() => Object.keys(localStorage));
    if (!r.storageKeys.some(k => k.includes('biologiya') && k.includes('v1_0_2'))) fail(scope, `Не найден новый ключ localStorage 1.0.2: ${r.storageKeys.join(', ')}`);

    const go = async n => { await page.evaluate(n => window.BiologyDemoTestApi.goTo(n), n); await page.waitForFunction(n => document.querySelector('.bio-question-number')?.textContent.trim() === `Задание ${n}`, n); };
    const answer = async n => page.evaluate(n => window.BiologyDemoTestApi.getSelectedTask(n).answer.canonical, n);
    const simple = new Set([1,3,4,5,9,13]);
    const structured = new Set([2,6,10,14,19,20]);
    const sequence = new Set([8,12,16]);
    const multiple = new Set([7,11,15,17,18,21]);
    for (let n = 1; n <= 21; n++) {
      await go(n); const code = await answer(n);
      if (simple.has(n)) {
        if (await page.locator('#bio-answer').count() !== 1) fail(scope, `Задание ${n}: нет простого поля`);
        await page.locator('#bio-answer').fill(code);
      } else if (structured.has(n)) {
        const sels = page.locator('[data-structured-select]');
        if (await sels.count() !== code.length) fail(scope, `Задание ${n}: ${await sels.count()} селектов вместо ${code.length}`);
        for (let i=0;i<code.length;i++) await sels.nth(i).selectOption(code[i]);
      } else if (sequence.has(n)) {
        if (await page.locator('[data-sequence-value]').count() !== code.length) fail(scope, `Задание ${n}: неверное число элементов последовательности`);
        for (const ch of code) await page.locator(`[data-sequence-value="${ch}"]`).click();
      } else if (multiple.has(n)) {
        if (await page.locator('[data-multi-value]').count() < code.length) fail(scope, `Задание ${n}: нет флажков`);
        for (const ch of code) await page.locator(`[data-multi-value="${ch}"]`).check();
      }
      const stored = await page.evaluate(n => window.BiologyDemoTestApi.getState().answers[n], n);
      if (stored !== code) fail(scope, `Задание ${n}: сохранён ответ ${stored}, ожидался ${code}`);
    }
    r.shortTotal = await page.evaluate(() => window.BiologyDemoTestApi.shortTotal());
    if (r.shortTotal !== 36) fail(scope, `Первая часть даёт ${r.shortTotal}/36`);

    await go(2); await page.reload({ waitUntil: 'domcontentloaded', timeout: 90000 });
    await page.waitForFunction(() => !!window.BiologyDemoTestApi, null, { timeout: 60000 });
    if (!await page.locator('#bio-continue-btn').isVisible().catch(() => false)) fail(scope, 'После перезагрузки нет продолжения попытки');
    else {
      await page.locator('#bio-continue-btn').click(); await page.waitForSelector('#bio-app.is-active');
      const restored = await page.evaluate(() => window.BiologyDemoTestApi.shortTotal());
      if (restored !== 36) fail(scope, `После перезагрузки восстановлено ${restored}/36`);
    }
    await page.evaluate(() => window.BiologyDemoTestApi.finishNow());
    await page.waitForSelector('#bio-results.is-active', { timeout: 10000 });
    const resultText = (await page.locator('#bio-results').innerText()).replace(/\s+/g,' ');
    r.result36 = /36\s*\/\s*36/.test(resultText);
    r.officialPending = /—\s*\/\s*57/.test(resultText);
    r.reviewCount = await page.locator('.bio-review-card').count();
    if (!r.result36 || !r.officialPending || r.reviewCount !== 28) fail(scope, `Итоговый экран: 36/36=${r.result36}, —/57=${r.officialPending}, карточек=${r.reviewCount}`);
    await page.screenshot({ path: path.join(outDir, 'biology-results-1440.png'), fullPage: true });

    await page.setViewportSize({ width: 320, height: 900 });
    await page.locator('#bio-retry').click(); await page.locator('#bio-start-btn').click(); await page.waitForSelector('#bio-app.is-active');
    for (let n=1;n<=28;n++) { await go(n); const ov = await overflow(page); if (ov > 3) fail(scope, `320 px, задание ${n}: overflow ${ov}px`); if (!await loadedImages(page,'#bio-question img')) fail(scope, `Задание ${n}: не загрузилось изображение`); }
    r.mobileOverflow = await overflow(page);
    r.status = report.failures.some(x => x.startsWith(`[${scope}]`)) ? 'NO-GO' : 'PASS';
  } catch (e) { fail(scope, e.stack || e.message); r.status='NO-GO'; try { await page.screenshot({path:path.join(outDir,'biology-failure.png'),fullPage:true}); } catch {} }
  await context.close();
}

async function auditSocial(browser) {
  const scope = 'Обществознание';
  const r = report.social = { url: 'https://eksamio.ru/ege/obshchestvoznaniye/demoversiya/', status: 'PENDING', pageErrors: [], consoleErrors: [], failedRequests: [], checks: [] };
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
  const page = await context.newPage(); diagnostics(page, r); page.on('dialog', d => d.accept());
  try {
    const response = await page.goto(r.url, { waitUntil: 'domcontentloaded', timeout: 90000 });
    r.httpStatus = response?.status() || null; if (r.httpStatus !== 200) fail(scope, `HTTP ${r.httpStatus}`);
    await page.waitForFunction(() => !!window.EKSAMIO_SOC_TEST, null, { timeout: 60000 });
    await page.evaluate(() => localStorage.clear()); await page.reload({ waitUntil: 'domcontentloaded' });
    await page.waitForFunction(() => !!window.EKSAMIO_SOC_TEST, null, { timeout: 60000 });
    await page.getByRole('button', { name: 'Начать экзамен' }).click();
    r.navCount = await page.getByRole('button', { name: /^Задание \d+$/ }).count();
    if (r.navCount !== 25) fail(scope, `В навигации ${r.navCount} заданий вместо 25`);
    r.storageKeys = await page.evaluate(() => Object.keys(localStorage));
    if (!r.storageKeys.includes('eksamio_ege_soc_demo_v3')) fail(scope, `Не найден новый ключ localStorage: ${r.storageKeys.join(', ')}`);
    const matching = {3:'32132',6:'24431',13:'21312',15:'21212'};
    const answers = {1:'46',2:'13',3:'32132',4:'146',5:'15',6:'24431',7:'2356',8:'125',9:'145',10:'234',11:'245',12:'123',13:'21312',14:'123',15:'21212',16:'125'};
    for (let n=1;n<=16;n++) {
      await page.getByRole('button',{name:`Задание ${n}`,exact:true}).click();
      if (await page.locator('#soc-short').count()) fail(scope, `Задание ${n}: осталось старое текстовое поле`);
      if (matching[n]) {
        const sels=page.locator('.soc-match-select'); if (await sels.count()!==5) fail(scope,`Задание ${n}: ${await sels.count()} селектов вместо 5`);
        for (let i=0;i<5;i++) await sels.nth(i).selectOption(matching[n][i]);
      } else {
        for (const ch of answers[n]) await page.getByRole('checkbox',{name:`Вариант ${ch}`}).check();
      }
      const code=(await page.locator('#soc-code').innerText()).replace(/\D/g,''); if (!code.includes(answers[n])) fail(scope,`Задание ${n}: код ${code}, ожидался ${answers[n]}`);
    }
    r.shortTotal = await page.evaluate(() => window.EKSAMIO_SOC_TEST.shortTotal()); if (r.shortTotal!==28) fail(scope,`Первая часть даёт ${r.shortTotal}/28`);
    await page.getByRole('button',{name:'Задание 3',exact:true}).click(); await page.reload({waitUntil:'domcontentloaded'});
    await page.waitForFunction(() => !!window.EKSAMIO_SOC_TEST, null, {timeout:60000});
    r.restoredTotal = await page.evaluate(() => window.EKSAMIO_SOC_TEST.shortTotal()); if (r.restoredTotal!==28) fail(scope,`После перезагрузки восстановлено ${r.restoredTotal}/28`);
    for (let n=17;n<=25;n++) { await page.getByRole('button',{name:`Задание ${n}`,exact:true}).click(); const tas=page.locator('textarea'); for (let i=0;i<await tas.count();i++) await tas.nth(i).fill('Развёрнутый учебный ответ для production-проверки.'); }
    await page.locator('#soc-finish').click(); await page.waitForTimeout(300);
    r.part1Result=await page.locator('#soc-part1-score').innerText(); r.totalResult=await page.locator('#soc-total-score').innerText();
    if (r.part1Result!=='28/28' || r.totalResult!=='—/58') fail(scope,`Итог: ${r.part1Result}, ${r.totalResult}`);
    for (let n=17;n<=25;n++) await page.getByText(`Задание ${n}`,{exact:true}).last().click();
    const s241=page.locator('select[data-task="24"][data-rubric="24.1"]'); const s242=page.locator('select[data-task="24"][data-rubric="24.2"]');
    await s241.selectOption('2'); if (!await s242.isDisabled() || await s242.inputValue()!=='0') fail(scope,'Зависимость 24.2 не блокируется при 24.1=2');
    await s241.selectOption('3'); if (await s242.isDisabled()) fail(scope,'24.2 не открывается при 24.1=3');
    await page.screenshot({path:path.join(outDir,'social-results-1440.png'),fullPage:true});

    await page.setViewportSize({width:320,height:900}); await page.getByRole('button',{name:'Пройти заново'}).click(); await page.getByRole('button',{name:'Начать экзамен'}).click();
    for (let n=1;n<=25;n++) { await page.getByRole('button',{name:`Задание ${n}`,exact:true}).click(); const ov=await overflow(page); if (ov>0) fail(scope,`320 px, задание ${n}: overflow ${ov}px`); if (!await loadedImages(page,'img')) fail(scope,`Задание ${n}: есть незагруженное изображение`); }
    r.status = report.failures.some(x => x.startsWith(`[${scope}]`)) ? 'NO-GO' : 'PASS';
  } catch(e) { fail(scope,e.stack||e.message); r.status='NO-GO'; try{await page.screenshot({path:path.join(outDir,'social-failure.png'),fullPage:true});}catch{} }
  await context.close();
}

const browser=await chromium.launch({headless:true});
await auditBiology(browser); await auditSocial(browser); await browser.close();
report.status=report.failures.length?'NO-GO':'PASS';
fs.writeFileSync(path.join(outDir,'report.json'),JSON.stringify(report,null,2));
fs.writeFileSync(path.join(outDir,'summary.txt'),`STATUS: ${report.status}\nBIOLOGY: ${report.biology.status}\nSOCIAL: ${report.social.status}\nFAILURES: ${report.failures.length}\n${report.failures.join('\n')}\n`);
console.log(JSON.stringify(report,null,2));
if(report.failures.length) process.exitCode=1;
