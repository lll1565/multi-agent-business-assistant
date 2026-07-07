const SAFE_STATUS_TEXT = {
  analyzing: "正在分析问题",
  db: "正在查询业务数据",
  api: "正在检索接口文档",
  web: "正在搜索网页信息",
  diagram: "正在生成图表",
  organizing: "正在整理结果",
};

const AGENT_STATUS = {
  npi_db_agent: "db",
  npi_api_agent: "api",
  npi_web_agent: "web",
  npi_diagram_agent: "diagram",
};

function statusKeyForStep(step = {}) {
  if (step.type === "status") {
    for (const [key, text] of Object.entries(SAFE_STATUS_TEXT)) {
      if (step.title === text) return key;
    }
    return "analyzing";
  }
  if (["thinking", "sub_thinking", "plan"].includes(step.type || "")) return "analyzing";

  const agent = String(step.agent || "");
  if (AGENT_STATUS[agent]) return AGENT_STATUS[agent];

  const blob = [step.type, step.title, step.detail].map((v) => String(v || "").toLowerCase()).join(" ");
  if (blob.includes("npi_db_agent") || blob.includes("sql") || blob.includes("数据库")) return "db";
  if (blob.includes("npi_api_agent") || blob.includes("api") || blob.includes("接口")) return "api";
  if (blob.includes("npi_web_agent") || blob.includes("web") || blob.includes("网页") || blob.includes("搜索")) return "web";
  if (blob.includes("npi_diagram_agent") || blob.includes("diagram") || blob.includes("图表") || blob.includes("流程图") || blob.includes("架构图")) return "diagram";
  if (["tool_result", "sub_tool_result", "sub_summary", "info"].includes(step.type || "")) return "organizing";
  return "analyzing";
}

export function buildSafeStatusLines(trace) {
  const steps = trace?.steps || [];
  const seen = new Set();
  const lines = [];

  for (const step of steps) {
    const key = statusKeyForStep(step);
    if (seen.has(key)) continue;
    seen.add(key);
    lines.push(SAFE_STATUS_TEXT[key]);
  }

  for (const agent of trace?.agents_used || []) {
    const key = AGENT_STATUS[String(agent || "")];
    if (!key || seen.has(key)) continue;
    seen.add(key);
    lines.push(SAFE_STATUS_TEXT[key]);
  }

  return lines;
}

function narrativeForStep(step) {
  return SAFE_STATUS_TEXT[statusKeyForStep(step)] || "";
}

/**
 * Build full narrative (for non-streaming display).
 */
export function buildStreamingNarrative(trace) {
  return buildSafeStatusLines(trace).join("\n\n");
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
  return buildSafeStatusLines(trace).join("\n\n");
}

/** @deprecated use appendStreamBuffer */
export function mergeThinkingText(current, incoming) {
  return appendStreamBuffer(current, incoming);
}
