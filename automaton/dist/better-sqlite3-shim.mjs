// Shim for better-sqlite3 that loads the native addon from /app/automaton/native/
// This avoids any dependency on node_modules being present in production.
import { createRequire } from 'module';
import { arch, platform } from 'os';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { existsSync } from 'fs';

const require = createRequire(import.meta.url);
const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, '..');

// Find the native addon
const a = arch(); // x64, arm64
const p = platform(); // linux, darwin
const paths = [
  join(root, 'native', `${p}-${a}`, 'better_sqlite3.node'),
  join(root, 'native', 'better_sqlite3.node'),
  join(root, 'node_modules', 'better-sqlite3', 'build', 'Release', 'better_sqlite3.node'),
];

let addonPath = null;
for (const p of paths) {
  if (existsSync(p)) { addonPath = p; break; }
}

if (!addonPath) {
  throw new Error(`better-sqlite3 native addon not found. Searched: ${paths.join(', ')}`);
}

// Load the native addon and the JS wrapper
const addon = require(addonPath);

// Re-export everything from the better-sqlite3 JS wrapper using the loaded addon
const DatabaseLib = require(join(root, 'node_modules', 'better-sqlite3', 'lib', 'database.js'));
const SqliteError = require(join(root, 'node_modules', 'better-sqlite3', 'lib', 'sqlite-error.js'));

// Patch the database constructor to use our loaded addon
const Database = function(...args) { return new DatabaseLib(addon, ...args); };
Object.setPrototypeOf(Database.prototype, DatabaseLib.prototype);
Database.SqliteError = SqliteError;

export default Database;
export { SqliteError };
