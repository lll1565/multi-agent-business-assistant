/** Node test shim for browser animation APIs used by usePacedEmitter. */
if (typeof globalThis.requestAnimationFrame !== "function") {
  globalThis.requestAnimationFrame = (cb) => setTimeout(() => cb(performance.now()), 0);
}
if (typeof globalThis.cancelAnimationFrame !== "function") {
  globalThis.cancelAnimationFrame = (id) => clearTimeout(id);
}
