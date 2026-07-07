import { onUnmounted, ref, watch } from "vue";

/**
 * DeepSeek-style typewriter: network bursts enqueue text; display reveals at fixed pace.
 */
export function useTypewriter(getTarget, options = {}) {
  const msPerChar = options.msPerChar ?? 28;
  const maxCharsPerFrame = options.maxCharsPerFrame ?? 2;
  const displayed = ref("");
  let rafId = null;
  let lastTs = 0;
  let charDebt = 0;

  function cancelAnim() {
    if (rafId != null) {
      cancelAnimationFrame(rafId);
      rafId = null;
    }
    lastTs = 0;
    charDebt = 0;
  }

  function flush() {
    cancelAnim();
    displayed.value = getTarget() || "";
  }

  function tick(now) {
    const target = getTarget() || "";

    if (!target) {
      displayed.value = "";
      cancelAnim();
      return;
    }

    if (!target.startsWith(displayed.value) && displayed.value.length > 0) {
      if (target.length < displayed.value.length) {
        displayed.value = target;
        cancelAnim();
        return;
      }
    }

    if (displayed.value.length >= target.length) {
      displayed.value = target;
      cancelAnim();
      return;
    }

    if (!lastTs) lastTs = now;
    const elapsed = Math.max(0, now - lastTs);
    lastTs = now;
    charDebt += elapsed / msPerChar;

    const toAdd = Math.min(
      maxCharsPerFrame,
      Math.floor(charDebt),
      target.length - displayed.value.length
    );
    if (toAdd > 0) {
      charDebt -= toAdd;
      displayed.value = target.slice(0, displayed.value.length + toAdd);
    }

    rafId = requestAnimationFrame(tick);
  }

  function ensureAnim() {
    const target = getTarget() || "";
    if (displayed.value.length >= target.length) {
      displayed.value = target;
      return;
    }
    if (rafId == null) {
      lastTs = 0;
      rafId = requestAnimationFrame(tick);
    }
  }

  watch(
    () => getTarget(),
    (next) => {
      if (!next) {
        displayed.value = "";
        cancelAnim();
        return;
      }
      ensureAnim();
    },
    { flush: "post" }
  );

  onUnmounted(cancelAnim);

  return { displayed, flush, ensureAnim };
}
