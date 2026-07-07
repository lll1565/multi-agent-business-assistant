/**
 * Clean model output before display (thinking tags, duplicates).
 */

const REDACTED_RE = /<think>[\s\S]*?<\/redacted_thinking>/gi;
const REDACTED_OPEN_RE = /<think>/gi;
const REDACTED_CLOSE_RE = /<\/redacted_thinking>/gi;

/** Remove redacted_thinking blocks and stray tags. */
export function stripRedactedThinking(text) {
  if (!text) return "";
  let out = text.replace(REDACTED_RE, "");
  out = out.replace(REDACTED_OPEN_RE, "").replace(REDACTED_CLOSE_RE, "");
  return out.replace(/\n{3,}/g, "\n\n").trim();
}

/** If plain text repeats content already inside removed tags, drop redundant paragraph. */
export function dedupeThinkingParagraph(text) {
  const cleaned = stripRedactedThinking(text);
  if (!cleaned) return "";
  const lines = cleaned.split("\n").map((l) => l.trim()).filter(Boolean);
  if (lines.length < 2) return cleaned;
  const first = lines[0];
  const dupIdx = lines.findIndex((l, i) => i > 0 && l === first);
  if (dupIdx > 0) return lines.slice(dupIdx).join("\n");
  return cleaned;
}

export function sanitizeAssistantText(text) {
  return dedupeThinkingParagraph(text || "");
}

export function sanitizeTraceStepDetail(detail, stepType) {
  let s = sanitizeAssistantText(detail);
  if (stepType === "thinking" && s.length > 280) {
    return `${s.slice(0, 280)}…`;
  }
  return s;
}
