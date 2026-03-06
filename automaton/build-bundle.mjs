#!/usr/bin/env node
/**
 * Anima Fund — esbuild bundler
 *
 * Bundles the entire Automaton engine into a single ESM file (dist/bundle.mjs).
 * All JavaScript dependencies are inlined. The only external dependency is the
 * better-sqlite3 native addon (.node file), which is loaded at runtime from
 * /app/automaton/native/<platform>-<arch>/better_sqlite3.node.
 *
 * The `bindings` npm package (used by better-sqlite3 to locate .node files)
 * is replaced by a custom shim that resolves from a known path relative to
 * the bundle, eliminating any need for node_modules at runtime.
 */
import esbuild from 'esbuild';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));

/**
 * Plugin: replace the `bindings` npm package with a shim that loads
 * native addons from /app/automaton/native/<platform>-<arch>/
 */
const bindingsPlugin = {
  name: 'bindings-shim',
  setup(build) {
    build.onResolve({ filter: /^bindings$/ }, () => ({
      path: 'bindings',
      namespace: 'bindings-shim',
    }));

    build.onLoad({ filter: /.*/, namespace: 'bindings-shim' }, () => ({
      contents: `
        const path = require('path');
        const fs = require('fs');

        module.exports = function bindings(addonName) {
          const arch = process.arch;     // x64, arm64
          const plat = process.platform; // linux, darwin

          // Search paths relative to the automaton root (/app/automaton)
          const root = path.resolve('/app/automaton');
          const candidates = [
            path.join(root, 'native', plat + '-' + arch, addonName),
            path.join(root, 'native', addonName),
          ];

          for (const candidate of candidates) {
            if (fs.existsSync(candidate)) {
              // Use process.dlopen for native addons — works without node_modules
              const mod = { exports: {} };
              process.dlopen(mod, candidate);
              return mod.exports;
            }
          }

          throw new Error(
            'Native addon "' + addonName + '" not found. ' +
            'Searched: ' + candidates.join(', ')
          );
        };
      `,
      loader: 'js',
    }));
  },
};

/**
 * Plugin: mark .node files as external (they can't be bundled)
 */
const nativeFilePlugin = {
  name: 'native-file-external',
  setup(build) {
    build.onResolve({ filter: /\.node$/ }, (args) => ({
      path: args.path,
      external: true,
    }));
  },
};

try {
  const result = await esbuild.build({
    entryPoints: [join(__dirname, 'src/index.ts')],
    bundle: true,
    platform: 'node',
    format: 'esm',
    target: 'node20',
    outfile: join(__dirname, 'dist/bundle.mjs'),
    banner: {
      js: 'import { createRequire } from "module"; const require = createRequire(import.meta.url);',
    },
    plugins: [bindingsPlugin, nativeFilePlugin],
    // Let esbuild handle everything — no external packages
    mainFields: ['module', 'main'],
    // Silence non-critical warnings
    logLevel: 'warning',
  });

  if (result.errors.length > 0) {
    console.error('Build errors:', result.errors);
    process.exit(1);
  }
  console.log('Bundle created: dist/bundle.mjs');
  console.log('Warnings:', result.warnings.length);
} catch (err) {
  console.error('Build failed:', err);
  process.exit(1);
}
