// CI-safe test: runs only the parity check that needs no personal data
// (synthetic cases through both the Python and the JS engines).
// The full `npm test` (run.mjs) also needs ../.venv and a real api_data/ folder.
import { execFileSync } from 'node:child_process';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const python = process.env.PYTHON || join(here, '..', '..', '.venv', 'bin', 'python');
const dir = mkdtempSync(join(tmpdir(), 'datastrap-parity-'));
const run = (cmd, args) => execFileSync(cmd, args, { stdio: 'inherit' });
try {
  run(python, [join(here, 'dump_synthetic.py'), dir]);
  run(process.execPath, [join(here, 'synthetic_parity.mjs'), dir]);
} finally {
  rmSync(dir, { recursive: true, force: true });
}
