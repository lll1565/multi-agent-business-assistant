/**
 * Fixed-rate character release — network/trace may burst in one tick;
 * UI only receives visible text at msPerChar pace (DeepSeek-style).
 */
export function createPacedEmitter(options = {}) {
  const msPerChar = options.msPerChar ?? 10;
  const maxPerFrame = options.maxPerFrame ?? 8;
  const followLatest = !!options.followLatest;
  const catchUpThreshold = options.catchUpThreshold ?? 100;
  const catchUpMaxPerFrame = options.catchUpMaxPerFrame ?? 24;
  const catchUpMinMsPerChar = options.catchUpMinMsPerChar ?? 6;

  function resolvePace(backlog) {
    if (!followLatest || backlog <= catchUpThreshold) {
      return { ms: msPerChar, max: maxPerFrame };
    }
    const ratio = Math.min(
      8,
      1 + (backlog - catchUpThreshold) / catchUpThreshold
    );
    return {
      ms: Math.max(catchUpMinMsPerChar, msPerChar / ratio),
      max: Math.min(catchUpMaxPerFrame, Math.round(maxPerFrame * ratio)),
    };
  }

  let queue = "";
  let visible = "";
  let sealed = false;
  let rafId = null;
  let lastTs = 0;
  let charDebt = 0;
  const drainedCbs = new Set();
  const updateCbs = new Set();

  function notifyUpdate() {
    for (const fn of updateCbs) fn(visible);
  }

  function isDrained() {
    return sealed && queue.length === 0;
  }

  function isPending() {
    return queue.length > 0;
  }

  function tryDrained() {
    if (!isDrained()) return;
    for (const fn of drainedCbs) fn();
  }

  function cancelAnim() {
    if (rafId != null) {
      cancelAnimationFrame(rafId);
      rafId = null;
    }
    lastTs = 0;
    charDebt = 0;
  }

  function tick(now) {
    rafId = null;
    if (!queue.length) {
      tryDrained();
      return;
    }

    if (!lastTs) lastTs = now;
    const elapsed = Math.max(0, now - lastTs);
    lastTs = now;
    const { ms, max } = resolvePace(queue.length);
    charDebt += elapsed / ms;

    const take = Math.min(max, Math.floor(charDebt), queue.length);
    if (take > 0) {
      charDebt -= take;
      visible += queue.slice(0, take);
      queue = queue.slice(take);
      notifyUpdate();
    }

    if (queue.length) {
      rafId = requestAnimationFrame(tick);
    } else {
      tryDrained();
    }
  }

  function schedule() {
    if (rafId == null) {
      lastTs = 0;
      rafId = requestAnimationFrame(tick);
    }
  }

  function feed(text) {
    if (!text) return;
    queue += text;
    schedule();
  }

  function seal() {
    sealed = true;
    if (!queue.length) tryDrained();
  }

  function onUpdate(fn) {
    updateCbs.add(fn);
    fn(visible);
    return () => updateCbs.delete(fn);
  }

  function onDrained(fn) {
    if (isDrained()) {
      fn();
      return () => {};
    }
    drainedCbs.add(fn);
    return () => drainedCbs.delete(fn);
  }

  function dispose() {
    cancelAnim();
    drainedCbs.clear();
    updateCbs.clear();
  }

  /** Release any queued characters immediately (error / teardown fallback). */
  function flushAll() {
    cancelAnim();
    if (queue) {
      visible += queue;
      queue = "";
      notifyUpdate();
    }
    if (sealed) tryDrained();
  }

  function reset() {
    cancelAnim();
    queue = "";
    visible = "";
    sealed = false;
    notifyUpdate();
  }

  return {
    feed,
    seal,
    reset,
    dispose,
    flushAll,
    onUpdate,
    onDrained,
    isDrained,
    isPending,
    get visible() {
      return visible;
    },
    get hasContent() {
      return !!(visible || queue);
    },
  };
}
