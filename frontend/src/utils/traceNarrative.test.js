import {describe, expect, it} from "vitest";
import {appendStreamBuffer} from "../utils/traceNarrative.js";

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
});
