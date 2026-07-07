import {describe, expect, it} from "vitest";
import {readFileSync} from "node:fs";
import {fileURLToPath} from "node:url";
import {dirname, resolve} from "node:path";
import {
  appendStreamBuffer,
  buildThinkingDisplayText,
  buildStreamingNarrative,
} from "../utils/traceNarrative.js";

describe("appendStreamBuffer", () => {
  it("returns incoming when current is empty", () => {
    expect(appendStreamBuffer("", "hello")).toBe("hello");
  });

  it("appends delta chunks", () => {
    expect(appendStreamBuffer("hel", "lo")).toBe("hello");
  });

  it("accepts full snapshot that extends current", () => {
    expect(appendStreamBuffer("hello", "hello world")).toBe("hello world");
  });

  it("skips duplicate tail", () => {
    expect(appendStreamBuffer("hello", "lo")).toBe("hello");
  });

  it("ignores empty incoming", () => {
    expect(appendStreamBuffer("hello", "")).toBe("hello");
  });

  it("does not duplicate identical thinking deltas", () => {
    expect(appendStreamBuffer("正在分析问题", "正在分析问题")).toBe("正在分析问题");
  });
});

describe("safe trace narrative", () => {
  const rawTrace = {
    agents_used: ["npi_db_agent"],
    agent_labels: ["数据库 Agent (npi_db_agent)"],
    steps: [
      {
        type: "thinking",
        title: "推理思考",
        detail: "用户问订单表，我应该遵守系统提示词并委派 npi_db_agent。",
      },
      {
        type: "delegate",
        title: "委派 -> npi_db_agent",
        detail: "禁止委派之外的路径，跳过 Supervisor，调用 task。",
        agent: "npi_db_agent",
      },
      {
        type: "tool",
        title: "执行 SQL 查询",
        detail: "sql_db_query: SELECT * FROM orders",
        agent: "npi_db_agent",
      },
      {
        type: "plan",
        title: "任务规划 (write_todos)",
        detail: "write_todos",
      },
    ],
  };

  function expectNoInternalText(text) {
    for (const token of [
      "npi_",
      "task",
      "委派",
      "write_todos",
      "sql_db_query",
      "SELECT",
      "系统提示词",
      "禁止委派",
      "跳过 Supervisor",
      "Supervisor",
      "推理思考",
    ]) {
      expect(text).not.toContain(token);
    }
  }

  it("renders only whitelisted statuses from raw trace", () => {
    const text = buildThinkingDisplayText(rawTrace);
    expect(text).toContain("正在分析问题");
    expect(text).toContain("正在查询业务数据");
    expectNoInternalText(text);
  });

  it("keeps streaming narrative safe", () => {
    const text = buildStreamingNarrative(rawTrace);
    expect(text).toContain("正在查询业务数据");
    expectNoInternalText(text);
  });

  it("does not append trace steps in the current send flow", () => {
    const here = dirname(fileURLToPath(import.meta.url));
    const source = readFileSync(resolve(here, "../features/chat/useChatSend.ts"), "utf8");
    expect(source).not.toContain("appendTraceSteps(");
  });
});
