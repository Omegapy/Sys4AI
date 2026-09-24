import { defineConfig } from 'vite';
import { prepareBuild, targets } from './scripts/package-runtime.mjs';

// Build-only code: fixed authored-input inventory and pre-output identity.
const prepared = prepareBuild(process.cwd());
export default defineConfig({
  base: './',
  publicDir: false,
  envDir: false,
  envPrefix: [],
  define: prepared.define,
  plugins: [prepared.plugin],
  build: {
    target: targets,
    outDir: 'dist',
    emptyOutDir: true,
    sourcemap: false,
    assetsInlineLimit: 0,
    modulePreload: { polyfill: false },
    rolldownOptions: {
      output: {
        entryFileNames: 'chunks/[name]-[hash].js',
        chunkFileNames: 'chunks/[name]-[hash].js',
        assetFileNames: 'chunks/[name]-[hash][extname]',
      },
    },
  },
});
