import { describe, expect, it } from "vitest";
import { createPacedEmitter } from "../composables/usePacedEmitter.js";

describe("createPacedEmitter", () => {
  it("feeds and releases visible text", async () => {
    const emitter = createPacedEmitter({ msPerChar: 0, maxPerFrame: 100 });
    const seen = [];
    emitter.onUpdate((v) => seen.push(v));

    emitter.feed("abc");
    emitter.flushAll();

    expect(emitter.visible).toBe("abc");
    expect(seen.at(-1)).toBe("abc");
    emitter.dispose();
  });

  it("seal marks drained when queue empty", () => {
    const emitter = createPacedEmitter({ msPerChar: 0, maxPerFrame: 100 });
    let drained = false;
    emitter.onDrained(() => {
      drained = true;
    });
    emitter.seal();
    expect(drained).toBe(true);
    emitter.dispose();
  });

  it("reset clears visible and queue", () => {
    const emitter = createPacedEmitter({ msPerChar: 0, maxPerFrame: 100 });
    emitter.feed("x");
    emitter.flushAll();
    emitter.reset();
    expect(emitter.visible).toBe("");
    expect(emitter.hasContent).toBe(false);
    emitter.dispose();
  });
});
