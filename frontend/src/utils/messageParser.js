/**
 * @deprecated 请使用 modules/message-blocks 与 modules/markdown
 * 保留 re-export 以兼容旧引用
 */
export {
  parseMessageBlocks as parseMessageContent,
  parseSqlToolResult,
} from "../modules/message-blocks/parser";

export { renderMarkdownHtml as formatTextHtml } from "../modules/markdown/renderer";
