import { onUnmounted, ref, watch } from "vue";
import { createPacedEmitter } from "./usePacedEmitter";

/**
 * Vue wrapper: source ref may burst-update; visible ref reveals at fixed pace.
 */
export function usePacedSource(source, options = {}) {
  const visible = ref("");
  const pending = ref(false);
  const emitter = createPacedEmitter({
    followLatest: options.followLatest,
    catchUpThreshold: options.catchUpThreshold,
    catchUpMaxPerFrame: options.catchUpMaxPerFrame,
    catchUpMinMsPerChar: options.catchUpMinMsPerChar,
    msPerChar: options.msPerChar,
    maxPerFrame: options.maxPerFrame,
  });
  let lastSource = "";

  const stopUpdate = emitter.onUpdate((v) => {
    visible.value = v;
    pending.value = emitter.isPending();
  });

  function syncSuffix(next) {
    const text = next || "";
    if (!text) {
      lastSource = "";
      emitter.reset();
      return;
    }
    if (text.startsWith(lastSource)) {
      const suffix = text.slice(lastSource.length);
      if (suffix) emitter.feed(suffix);
    } else {
      emitter.reset();
      emitter.feed(text);
    }
    lastSource = text;
    pending.value = emitter.isPending();
  }

  watch(
    source,
    (next) => syncSuffix(next),
    { immediate: true }
  );

  function seal() {
    emitter.seal();
    pending.value = emitter.isPending();
  }

  function flush() {
    emitter.flushAll();
    pending.value = false;
  }

  function onDrained(fn) {
    return emitter.onDrained(fn);
  }

  onUnmounted(() => {
    stopUpdate();
    emitter.dispose();
  });

  return { visible, pending, seal, flush, onDrained, emitter };
}
