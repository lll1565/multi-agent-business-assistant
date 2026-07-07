import { describe, expect, it } from "vitest";
import { parseMessageBlocks } from "./parser.js";
import { BLOCK_TYPES } from "./types.js";

describe("parseMessageBlocks", () => {
  it("returns empty text block for blank input", () => {
    const blocks = parseMessageBlocks("");
    expect(blocks).toHaveLength(1);
    expect(blocks[0].type).toBe(BLOCK_TYPES.TEXT);
  });

  it("parses plain markdown text", () => {
    const blocks = parseMessageBlocks("Hello **world**");
    expect(blocks.some((b) => b.type === BLOCK_TYPES.TEXT)).toBe(true);
    const text = blocks.find((b) => b.type === BLOCK_TYPES.TEXT);
    expect(text.content).toContain("Hello");
  });

  it("parses fenced code blocks", () => {
    const blocks = parseMessageBlocks("```python\nprint(1)\n```");
    const code = blocks.find((b) => b.type === BLOCK_TYPES.CODE);
    expect(code).toBeDefined();
    expect(code.content).toContain("print(1)");
  });
});
