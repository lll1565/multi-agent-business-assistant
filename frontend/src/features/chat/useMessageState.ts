import {
  appendStreamBuffer,
  appendTraceSteps,
  buildThinkingDisplayText,
} from "../../utils/traceNarrative.js";
import type { ChatMessage, ReasoningTrace } from "./types";

export function useMessageState() {
  function isHistoricalMessage(msg: ChatMessage): boolean {
    if (!msg || msg.role !== "assistant") return false;
    if (msg.streaming) return false;
    const id = String(msg.id || "");
    return id.length > 0 && !id.startsWith("tmp-");
  }

  function normalizeMessage(m: ChatMessage): ChatMessage {
    const trace = m.trace || null;
    const liveThinking =
      (m.liveThinking || "").trim() || buildThinkingDisplayText(trace) || "";
    return {
      ...m,
      trace,
      liveThinking,
      answerUnlocked: m.answerUnlocked ?? true,
      answerStreaming: false,
      streaming: false,
      _thinkingSealed: true,
      _thinkingRevealComplete: true,
    };
  }

  function syncAnswerContent(msg: ChatMessage): void {
    if (!msg._pendingAnswer) return;
    if (!msg.answerUnlocked) return;
    if ((msg._pendingAnswer || "").length > (msg.content || "").length) {
      msg.content = msg._pendingAnswer;
      msg._pendingAnswer = "";
      msg.answerStreaming = true;
    }
  }

  function flushPendingAnswer(
    msg: ChatMessage,
    scrollToBottom: () => void | Promise<void>,
  ): void {
    if (msg.answerUnlocked) return;
    msg.answerUnlocked = true;
    msg.answerStreaming = true;
    if (msg._pendingAnswer) {
      msg.content = msg._pendingAnswer;
      msg._pendingAnswer = "";
    }
    void scrollToBottom();
  }

  function startAnswerPhase(
    msg: ChatMessage,
    scrollToBottom: () => void | Promise<void>,
  ): void {
    if (msg.answerUnlocked) {
      syncAnswerContent(msg);
      return;
    }
    if (!msg._thinkingSealed || !msg._thinkingRevealComplete) return;
    flushPendingAnswer(msg, scrollToBottom);
  }

  function onThinkingRevealDone(
    msg: ChatMessage,
    scrollToBottom: () => void | Promise<void>,
  ): void {
    msg._thinkingRevealComplete = true;
    startAnswerPhase(msg, scrollToBottom);
  }

  function onAnswerRevealDone(msg: ChatMessage): void {
    msg.answerStreaming = false;
  }

  function finalizeAssistantMessage(
    msg: ChatMessage,
    scrollToBottom: () => void | Promise<void>,
  ): void {
    if (!msg) return;
    if (!msg.liveThinking?.trim() && msg.trace) {
      const fromTrace = buildThinkingDisplayText(msg.trace as ReasoningTrace);
      if (fromTrace) msg.liveThinking = fromTrace;
    }
    msg.streaming = false;
    if (!msg._thinkingSealed) msg._thinkingSealed = true;

    if (!msg.liveThinking?.trim()) {
      msg._thinkingRevealComplete = true;
      startAnswerPhase(msg, scrollToBottom);
    }
  }

  function appendAnswerChunk(msg: ChatMessage, chunk: string): void {
    if (!chunk) return;
    if (!msg.answerUnlocked) {
      msg._pendingAnswer = appendStreamBuffer(msg._pendingAnswer || "", chunk);
      return;
    }
    msg.content = appendStreamBuffer(msg.content || "", chunk);
    msg.answerStreaming = true;
  }

  return {
    isHistoricalMessage,
    normalizeMessage,
    onThinkingRevealDone,
    startAnswerPhase,
    onAnswerRevealDone,
    finalizeAssistantMessage,
    appendAnswerChunk,
    appendTraceSteps,
  };
}

export type MessageState = ReturnType<typeof useMessageState>;
