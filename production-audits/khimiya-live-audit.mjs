import fs from 'node:fs';
import path from 'node:path';

const outDir = process.env.AUDIT_OUT || '/tmp/khimiya-live-audit';
fs.rmSync(outDir, { recursive: true, force: true });
fs.mkdirSync(outDir, { recursive: true });

const inputs = [
  'matematika-source-2025',
  'ege-matematika-baza-demoversiya-v2.zip',
  'ege-matematika-profil-demoversiya-VERIFIED-PACKAGE-v2.zip'
];
for (const src of inputs) {
  const dst = path.join(outDir, path.basename(src));
  fs.cpSync(src, dst, { recursive: true });
}
fs.writeFileSync(path.join(outDir, 'EXPORT-README.txt'), 'Temporary artifact export for the final 2025 mathematics source-fidelity audit. Do not merge this branch.\n');
console.log('Exported 2025 mathematics audit inputs.');
