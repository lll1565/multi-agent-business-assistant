import { computed, ref, watch } from "vue";
import { THEME_MODES, THEME_STORAGE_KEY } from "./constants";

function readStoredMode() {
  try {
    const v = localStorage.getItem(THEME_STORAGE_KEY);
    if (v === THEME_MODES.DARK || v === THEME_MODES.LIGHT || v === THEME_MODES.SYSTEM) {
      return v;
    }
  } catch {
    /* ignore */
  }
  return THEME_MODES.SYSTEM;
}

function systemPrefersDark() {
  return window.matchMedia?.("(prefers-color-scheme: dark)")?.matches ?? false;
}

function resolveIsDark(mode) {
  if (mode === THEME_MODES.DARK) return true;
  if (mode === THEME_MODES.LIGHT) return false;
  return systemPrefersDark();
}

function applyDomTheme(isDark) {
  const root = document.documentElement;
  root.classList.toggle("dark", isDark);
  root.dataset.theme = isDark ? "dark" : "light";
}

const mode = ref(readStoredMode());
const isDark = computed(() => resolveIsDark(mode.value));

let mediaQuery;
let mediaHandler;
let systemListenerBound = false;

function bindSystemListener() {
  if (systemListenerBound || !window.matchMedia) return;
  systemListenerBound = true;
  mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
  mediaHandler = () => {
    if (mode.value === THEME_MODES.SYSTEM) applyDomTheme(resolveIsDark(mode.value));
  };
  mediaQuery.addEventListener?.("change", mediaHandler);
}

function persistMode(next) {
  mode.value = next;
  try {
    localStorage.setItem(THEME_STORAGE_KEY, next);
  } catch {
    /* ignore */
  }
}

watch(
  isDark,
  (dark) => applyDomTheme(dark),
  { immediate: true }
);

export function useTheme() {
  function setMode(next) {
    persistMode(next);
  }

  function toggle() {
    setMode(isDark.value ? THEME_MODES.LIGHT : THEME_MODES.DARK);
  }

  return {
    mode,
    isDark,
    setMode,
    toggle,
    THEME_MODES,
  };
}

/** 应用启动时同步主题（main.js 调用） */
export function initTheme() {
  const stored = readStoredMode();
  mode.value = stored;
  applyDomTheme(resolveIsDark(stored));
  bindSystemListener();
}
