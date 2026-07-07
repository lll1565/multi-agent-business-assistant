/**
 * 表格块 → CSV 与导出/复制
 */

/** @param {unknown} value */
function escapeCsvCell(value) {
  const s = String(value ?? "");
  if (/[",\n\r]/.test(s)) {
    return `"${s.replace(/"/g, '""')}"`;
  }
  return s;
}

/**
 * @param {{ columns: { prop: string, label: string }[], rows: Record<string, unknown>[] }} block
 */
export function tableBlockToCsv(block) {
  const cols = block?.columns || [];
  const rows = block?.rows || [];
  if (!cols.length) return "";

  const header = cols.map((c) => escapeCsvCell(c.label)).join(",");
  const body = rows.map((row) =>
    cols.map((c) => escapeCsvCell(row[c.prop])).join(",")
  );
  return [header, ...body].join("\r\n");
}

/**
 * @param {string} filename
 * @param {string} text
 * @param {string} [mime]
 */
export function downloadTextFile(filename, text, mime = "text/csv;charset=utf-8") {
  const blob = new Blob(["\ufeff", text], { type: mime });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

/** @param {string} text */
export async function copyTextToClipboard(text) {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text);
    return;
  }
  const ta = document.createElement("textarea");
  ta.value = text;
  ta.style.position = "fixed";
  ta.style.left = "-9999px";
  document.body.appendChild(ta);
  ta.select();
  document.execCommand("copy");
  document.body.removeChild(ta);
}

/**
 * @param {{ columns: { prop: string, label: string }[], rows: Record<string, unknown>[], title?: string }} block
 */
export function buildTableExportFilename(block) {
  const title = (block?.title || "export").replace(/[^\w\u4e00-\u9fa5-]+/g, "_");
  const date = new Date().toISOString().slice(0, 10);
  return `${title}_${date}.csv`;
}
