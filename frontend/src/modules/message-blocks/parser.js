/**
 * 将助手原文解析为可渲染块（text / table / code）
 */
import { sanitizeAssistantText } from "../../utils/textSanitizer";
import { resolveTableTitle } from "../../utils/tableDisplay";
import { BLOCK_TYPES } from "./types";

function tryParseJson(str) {
  try {
    return JSON.parse(str);
  } catch {
    return null;
  }
}

function rowsToTable(data) {
  if (!data) return null;

  if (Array.isArray(data) && data.length > 0) {
    if (typeof data[0] === "object" && data[0] !== null && !Array.isArray(data[0])) {
      const columns = Object.keys(data[0]).map((key) => ({
        prop: key,
        label: key,
        minWidth: 100,
      }));
      return { columns, rows: data };
    }
    if (Array.isArray(data[0])) {
      const columns = data[0].map((_, i) => ({
        prop: `col_${i}`,
        label: `列${i + 1}`,
        minWidth: 90,
      }));
      const rows = data.slice(1).map((row) => {
        const obj = {};
        row.forEach((cell, i) => {
          obj[`col_${i}`] = cell;
        });
        return obj;
      });
      return { columns, rows };
    }
  }

  if (data.columns && data.rows) {
    const cols = data.columns.map((c) => ({
      prop: String(c),
      label: String(c),
      minWidth: 100,
    }));
    const rows = data.rows.map((row) => {
      if (Array.isArray(row)) {
        const obj = {};
        data.columns.forEach((c, i) => {
          obj[String(c)] = row[i];
        });
        return obj;
      }
      return row;
    });
    return { columns: cols, rows };
  }

  return null;
}

function parseMarkdownTable(text) {
  const lines = text.trim().split("\n");
  if (lines.length < 2) return null;

  const headerLine = lines[0];
  const sepLine = lines[1];
  if (!headerLine.includes("|") || !/^\|?[\s\-:|]+\|?$/.test(sepLine)) {
    return null;
  }

  const splitRow = (line) =>
    line
      .trim()
      .replace(/^\|/, "")
      .replace(/\|$/, "")
      .split("|")
      .map((c) => c.trim());

  const headers = splitRow(headerLine);
  if (headers.length < 2) return null;

  const columns = headers.map((h, i) => ({
    prop: `col_${i}`,
    label: h || `列${i + 1}`,
    minWidth: 100,
  }));

  const rows = [];
  for (let i = 2; i < lines.length; i++) {
    if (!lines[i].includes("|")) break;
    const cells = splitRow(lines[i]);
    const row = {};
    columns.forEach((col, idx) => {
      row[col.prop] = cells[idx] ?? "";
    });
    rows.push(row);
  }

  if (rows.length === 0) return null;
  return { columns, rows };
}

function extractMarkdownTables(text) {
  const blocks = [];
  const regex = /(?:^|\n)(\|[^\n]+\|\n\|[-:\s|]+\|\n(?:\|[^\n]+\|\n?)+)/g;
  let lastIndex = 0;
  let match;

  while ((match = regex.exec(text)) !== null) {
    const before = text.slice(lastIndex, match.index).trim();
    if (before) blocks.push({ type: BLOCK_TYPES.TEXT, content: before });

    const table = parseMarkdownTable(match[1].trim());
    if (table) {
      blocks.push({
        type: BLOCK_TYPES.TABLE,
        ...table,
        title: resolveTableTitle({ columns: table.columns }),
      });
    } else {
      blocks.push({ type: BLOCK_TYPES.TEXT, content: match[1].trim() });
    }
    lastIndex = match.index + match[0].length;
  }

  const rest = text.slice(lastIndex).trim();
  if (rest) blocks.push({ type: BLOCK_TYPES.TEXT, content: rest });

  return blocks.length ? blocks : [{ type: BLOCK_TYPES.TEXT, content: text }];
}

function extractJsonTables(text) {
  const blocks = [];
  const jsonRegex = /```(?:json)?\s*([\s\S]*?)```/gi;
  let lastIndex = 0;
  let match;

  while ((match = jsonRegex.exec(text)) !== null) {
    const before = text.slice(lastIndex, match.index).trim();
    if (before) {
      blocks.push(...extractMarkdownTables(before));
    }

    const parsed = tryParseJson(match[1].trim());
    const table = rowsToTable(parsed);
    if (table && table.rows?.length) {
      blocks.push({
        type: BLOCK_TYPES.TABLE,
        ...table,
        title: resolveTableTitle({ columns: table.columns }),
      });
    } else {
      blocks.push({
        type: BLOCK_TYPES.CODE,
        content: match[1].trim(),
        language: "json",
      });
    }
    lastIndex = match.index + match[0].length;
  }

  const rest = text.slice(lastIndex).trim();
  if (rest) blocks.push(...extractMarkdownTables(rest));

  return blocks.length ? blocks : extractMarkdownTables(text);
}

/** @param {string} detail */
export function parseSqlToolResult(detail) {
  if (!detail) return null;
  const trimmed = detail.trim();

  let parsed = tryParseJson(trimmed);
  if (parsed) return rowsToTable(parsed);

  const jsonMatch = trimmed.match(/\{[\s\S]*\}|\[[\s\S]*\]/);
  if (jsonMatch) {
    parsed = tryParseJson(jsonMatch[0]);
    if (parsed) return rowsToTable(parsed);
  }

  if (trimmed.includes("|") && trimmed.includes("---")) {
    const table = parseMarkdownTable(trimmed);
    if (table) return table;
  }

  const tupleList = trimmed.match(/^\[([\s\S]+)\]$/);
  if (tupleList) {
    const items = [...trimmed.matchAll(/\(['"]?([^'")]+)['"]?\)/g)].map((m) => m[1]);
    if (items.length >= 1) {
      return {
        columns: [{ prop: "name", label: "名称", minWidth: 120 }],
        rows: items.map((name) => ({ name: name.trim() })),
      };
    }
  }

  return null;
}

/** @param {string} text */
export function parseMessageBlocks(text) {
  const cleaned = sanitizeAssistantText(text);
  if (!cleaned) return [{ type: BLOCK_TYPES.TEXT, content: "" }];
  return extractJsonTables(cleaned);
}

/** @param {import('./types').MessageBlock} block */
export function blockHasContent(block) {
  if (block.type === BLOCK_TYPES.TEXT) return !!(block.content || "").trim();
  if (block.type === BLOCK_TYPES.TABLE) return (block.rows || []).length > 0;
  return !!(block.content || "").trim();
}

/** @param {import('./types').MessageBlock} block @param {number} i */
export function blockStableKey(block, i) {
  if (block.type === BLOCK_TYPES.TABLE) {
    return `t-${i}-${block.rows?.length}-${block.columns?.length}`;
  }
  if (block.type === BLOCK_TYPES.CODE) {
    return `c-${i}-${(block.content || "").length}`;
  }
  return `x-${i}-${(block.content || "").length}`;
}
