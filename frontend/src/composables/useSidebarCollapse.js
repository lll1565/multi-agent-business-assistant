import { ref, watch } from "vue";

const STORAGE_KEY = "multi_agent_sidebar_collapsed";

function readStored() {
  try {
    return localStorage.getItem(STORAGE_KEY) === "1";
  } catch {
    return false;
  }
}

/** 侧栏折叠（类似 DeepSeek：收起后主区全宽，顶栏可再展开） */
export function useSidebarCollapse() {
  const collapsed = ref(readStored());

  watch(collapsed, (v) => {
    try {
      localStorage.setItem(STORAGE_KEY, v ? "1" : "0");
    } catch {
      /* ignore */
    }
  });

  function toggle() {
    collapsed.value = !collapsed.value;
  }

  function expand() {
    collapsed.value = false;
  }

  return { collapsed, toggle, expand };
}
