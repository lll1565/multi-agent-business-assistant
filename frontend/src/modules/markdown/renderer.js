import MarkdownIt from "markdown-it";
import hljs from "highlight.js";
import DOMPurify from "dompurify";
import { sanitizeAssistantText } from "../../utils/textSanitizer";

const ALLOWED_TAGS = [
  "h1", "h2", "h3", "h4", "h5", "h6", "p", "br", "hr",
  "ul", "ol", "li", "blockquote", "pre", "code", "span",
  "strong", "em", "a", "table", "thead", "tbody", "tr", "th", "td",
];

const ALLOWED_ATTR = ["href", "target", "rel", "class"];

let mdInstance;

function getMarkdownIt() {
  if (mdInstance) return mdInstance;

  mdInstance = new MarkdownIt({
    html: false,
    linkify: true,
    breaks: true,
    typographer: true,
    highlight(str, lang) {
      if (lang && hljs.getLanguage(lang)) {
        try {
          return `<pre class="hljs"><code class="language-${lang}">${hljs.highlight(str, { language: lang }).value}</code></pre>`;
        } catch {
          /* fall through */
        }
      }
      return `<pre class="hljs"><code>${hljs.highlightAuto(str).value}</code></pre>`;
    },
  });

  const defaultLinkOpen =
    mdInstance.renderer.rules.link_open ||
    ((tokens, idx, options, env, self) => self.renderToken(tokens, idx, options));

  mdInstance.renderer.rules.link_open = (tokens, idx, options, env, self) => {
    tokens[idx].attrSet("target", "_blank");
    tokens[idx].attrSet("rel", "noopener noreferrer");
    return defaultLinkOpen(tokens, idx, options, env, self);
  };

  return mdInstance;
}

/**
 * @param {string} text
 * @returns {string} 安全 HTML
 */
/** HTTP 方法徽章（API 文档表格中的 GET/POST 等） */
function enhanceApiDocHtml(html) {
  if (!html) return html;
  let out = html;

  const methodBadge = (method) =>
    new RegExp(
      `<td>(\\s*)<strong>${method}</strong>(\\s*)</td>`,
      "gi"
    );

  const methods = [
    ["GET", "http-get"],
    ["POST", "http-post"],
    ["PUT", "http-put"],
    ["DELETE", "http-delete"],
    ["PATCH", "http-patch"],
  ];

  for (const [method, cls] of methods) {
    out = out.replace(
      methodBadge(method),
      `<td><span class="http-badge ${cls}">${method}</span></td>`
    );
  }

  if (out.includes("### 请求参数") || out.includes("## API 接口")) {
    out = `<div class="api-doc-surface">${out}</div>`;
  }

  return out;
}

export function renderMarkdownHtml(text) {
  const cleaned = sanitizeAssistantText(text);
  if (!cleaned) return "";

  const raw = getMarkdownIt().render(cleaned);
  const safe = DOMPurify.sanitize(raw, {
    ALLOWED_TAGS: [...ALLOWED_TAGS, "div"],
    ALLOWED_ATTR,
  });
  return enhanceApiDocHtml(safe);
}
