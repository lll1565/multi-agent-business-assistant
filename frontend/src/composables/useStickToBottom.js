import { ref } from "vue";

/**
 * 容器贴底跟随：用户未上滑时，内容变长自动滚到最新行。
 */
export function useStickToBottom(containerRef, options = {}) {
  const threshold = options.threshold ?? 40;
  const stuck = ref(true);

  function onScroll() {
    const el = containerRef.value;
    if (!el) return;
    const gap = el.scrollHeight - el.scrollTop - el.clientHeight;
    stuck.value = gap <= threshold;
  }

  function scrollToBottomIfStuck(force = false) {
    const el = containerRef.value;
    if (!el) return;
    if (!force && !stuck.value) return;
    el.scrollTop = el.scrollHeight;
    stuck.value = true;
  }

  return { stuck, onScroll, scrollToBottomIfStuck };
}
