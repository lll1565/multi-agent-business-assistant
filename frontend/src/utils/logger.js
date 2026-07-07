/**
 * Frontend logger — browser console + optional verbose mode.
 * Enable: localStorage.setItem("MAS_DEBUG", "1")
 */

const DEBUG =
  import.meta.env.DEV ||
  (typeof localStorage !== "undefined" &&
    localStorage.getItem("MAS_DEBUG") === "1");

function ts() {
  return new Date().toISOString().slice(11, 23);
}

function prefix(level) {
  return `[${ts()}][chat-ui][${level}]`;
}

export const logger = {
  debug(...args) {
    if (DEBUG) console.debug(prefix("DEBUG"), ...args);
  },
  info(...args) {
    console.info(prefix("INFO"), ...args);
  },
  warn(...args) {
    console.warn(prefix("WARN"), ...args);
  },
  error(...args) {
    console.error(prefix("ERROR"), ...args);
  },
};
