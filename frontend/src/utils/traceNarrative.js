import {sanitizeAssistantText, sanitizeTraceStepDetail} from "./textSanitizer";

function narrativeForStep(step, { live = false } = {}) {
  const t = step.type || "";
  if (t === "thinking" || t === "sub_thinking") {
    const d = live
      ? sanitizeAssistantText(step.detail)
      : sanitizeTraceStepDetail(step.detail, t);
    return d || "";
  }
  if (t === "delegate") {
    return step.detail?.trim() || step.title || "";
  }
  if (t === "tool" || t === "sub_tool") {
    return step.title || "";
  }
  if (t === "plan") {
    return live
      ? sanitizeAssistantText(step.detail)
      : sanitizeTraceStepDetail(step.detail, t);
  }
  return "";
}

/**
 * Build full narrative (for non-streaming display).
 */
export function buildStreamingNarrative(trace) {
  if (!trace?.steps?.length) return "";
  return trace.steps
    .map((s) => narrativeForStep(s, { live: true }))
    .filter(Boolean)
    .join("\n\n");
}

/**
 * Append-only buffer: network/trace chunks enqueue; typewriter reveals left-to-right.
 */
export function appendStreamBuffer(current, incoming) {
  if (!incoming) return current || "";
  const cur = current || "";
  if (!cur) return incoming;
  // Full snapshot that extends current (e.g. reply event)
  if (incoming.startsWith(cur)) return incoming;
  // Avoid duplicating tail
  if (cur.endsWith(incoming)) return cur;
  return cur + incoming;
}

/**
 * Append only NEW trace steps since last index (incremental thinking stream).
 */
export function appendTraceSteps(current, trace, fromStepIndex = 0) {
  const steps = trace?.steps || [];
  let text = current || "";
  let next = fromStepIndex;

  for (let i = fromStepIndex; i < steps.length; i++) {
    const piece = narrativeForStep(steps[i], { live: true });
    if (!piece) {
      next = i + 1;
      continue;
    }
    if (text && !text.endsWith("\n\n")) text += "\n\n";
    text += piece;
    next = i + 1;
  }

  return { text, nextStepIndex: next };
}

/**
 * Narrative delta for newly arrived trace steps only (for paced thinking feed).
 */
export function nextTraceNarrative(trace, fromStepIndex = 0) {
  const steps = trace?.steps || [];
  let piece = "";
  let next = fromStepIndex;

  for (let i = fromStepIndex; i < steps.length; i++) {
    const part = narrativeForStep(steps[i], { live: true });
    if (!part) {
      next = i + 1;
      continue;
    }
    if (piece && !piece.endsWith("\n\n")) piece += "\n\n";
    piece += part;
    next = i + 1;
  }

  return { piece, nextStepIndex: next };
}

/** 历史消息：从 trace 还原思考正文 */
export function buildThinkingDisplayText(trace) {
  if (!trace?.steps?.length) return "";
  return trace.steps
    .map((s) => narrativeForStep(s, { live: false }))
    .filter(Boolean)
    .join("\n\n");
}

/** @deprecated use appendStreamBuffer */
export function mergeThinkingText(current, incoming) {
  return appendStreamBuffer(current, incoming);
}
