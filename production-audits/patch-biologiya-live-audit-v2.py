from pathlib import Path
import sys

if len(sys.argv) != 3:
    raise SystemExit("Usage: patch-biologiya-live-audit-v2.py INPUT OUTPUT")

source = Path(sys.argv[1]).read_text(encoding="utf-8")

old_self = """    const before = (await page.locator('#bio-self-total').innerText()).trim();
    await page.locator('[data-self-task=\"22\"]').first().check();
    const after = (await page.locator('#bio-self-total').innerText()).trim();
    if (before === after) fail(`[${label}] Учебная самооценка не обновляется`);
"""
new_self = """    const before = (await page.locator('#bio-self-total').innerText()).trim();
    const criteria = page.locator('[data-self-task=\"22\"]');
    for (let i = 0; i < Math.min(3, await criteria.count()); i++) await criteria.nth(i).check();
    const after = (await page.locator('#bio-self-total').innerText()).trim();
    if (before === after) fail(`[${label}] Учебная самооценка не обновляется после выбора достаточного набора критериев`);
"""
if old_self not in source:
    raise SystemExit("Self-assessment assertion block not found")
source = source.replace(old_self, new_self, 1)

old_variants = """const expectedVariants = {
  'variants-all-1': { 4: 'Вариант 1', 5: 'Вариант 1', 6: 'Вариант 1', 24: 'Вариант 1', 27: 'Вариант 1' },
  'variants-all-2': { 4: 'Вариант 2', 5: 'Вариант 2', 6: 'Вариант 2', 24: 'Вариант 2', 27: 'Вариант 2' },
  'variant-27-3': { 27: 'Вариант 3' },
  'variant-27-4': { 27: 'Вариант 4' }
};
"""
new_variants = """const expectedVariants = {
  'variants-all-1': { 4: 'Официальный пример 1 из 2', 5: 'Официальный комплект рисунков 1 из 2', 6: 'Официальный комплект рисунков 1 из 2', 24: 'Официальный пример 1 из 2', 27: 'Официальный пример 1 из 4' },
  'variants-all-2': { 4: 'Официальный пример 2 из 2', 5: 'Официальный комплект рисунков 2 из 2', 6: 'Официальный комплект рисунков 2 из 2', 24: 'Официальный пример 2 из 2', 27: 'Официальный пример 2 из 4' },
  'variant-27-3': { 27: 'Официальный пример 3 из 4' },
  'variant-27-4': { 27: 'Официальный пример 4 из 4' }
};
"""
if old_variants not in source:
    raise SystemExit("Variant expectation block not found")
source = source.replace(old_variants, new_variants, 1)

Path(sys.argv[2]).write_text(source, encoding="utf-8")
