/** @typedef {'text' | 'table' | 'code'} MessageBlockType */

/** @typedef {{ prop: string, label: string, minWidth?: number }} TableColumn */

/**
 * @typedef {Object} TextBlock
 * @property {'text'} type
 * @property {string} content
 */

/**
 * @typedef {Object} TableBlock
 * @property {'table'} type
 * @property {TableColumn[]} columns
 * @property {Record<string, unknown>[]} rows
 * @property {string} [title]
 */

/**
 * @typedef {Object} CodeBlock
 * @property {'code'} type
 * @property {string} content
 * @property {string} [language]
 */

/** @typedef {TextBlock | TableBlock | CodeBlock} MessageBlock */

export const BLOCK_TYPES = {
  TEXT: "text",
  TABLE: "table",
  CODE: "code",
};
