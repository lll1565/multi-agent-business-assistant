import { nextTick, type Ref } from "vue";
import { ElMessage } from "element-plus";
import { sendSessionChatStream } from "../../api/chat";
import { logger } from "../../utils/logger.js";
import { appendStreamBuffer } from "../../utils/traceNarrative.js";
import type { MessageState } from "./useMessageState";
import type { ChatMessage, ReasoningTrace, StreamDoneEvent, StreamErrorEvent } from "./types";

interface UseChatSendOptions {
  messages: Ref<ChatMessage[]>;
  input: Ref<string>;
  loading: Ref<boolean>;
  currentSessionId: Ref<string | null>;
  loadSessions: () => Promise<void>;
  scrollToBottom: () => void | Promise<void>;
  messageState: MessageState;
  setOnline: (online: boolean) => void;
}

function formatNetworkError(err: unknown): string {
  const e = err as {
    response?: { data?: { error?: string; detail?: string } };
    message?: string;
  };
  const detail =
    e.response?.data?.error ||
    e.response?.data?.detail ||
    e.message ||
    "网络错误";
  return `请求失败：${detail}（请确认后端已启动，见控制台与 data/logs/app.log）`;
}

export function useChatSend({
  messages,
  input,
  loading,
  currentSessionId,
  loadSessions,
  scrollToBottom,
  messageState,
  setOnline,
}: UseChatSendOptions) {
  const { appendAnswerChunk, finalizeAssistantMessage } = messageState;

  function findAssistantIndex(assistantId: string): number {
    return messages.value.findIndex((m) => m.id === assistantId);
  }

  async function send(): Promise<void> {
    const text = input.value.trim();
    if (!text || loading.value || !currentSessionId.value) return;

    const sid = currentSessionId.value;
    messages.value.push({
      id: `tmp-u-${Date.now()}`,
      role: "user",
      content: text,
      created_at: new Date().toISOString(),
    });
    input.value = "";
    loading.value = true;

    const assistantId = `tmp-a-${Date.now()}`;
    messages.value.push({
      id: assistantId,
      role: "assistant",
      content: "",
      liveThinking: "",
      trace: { agents_used: [], agent_labels: [], steps: [] },
      created_at: new Date().toISOString(),
      streaming: true,
      answerUnlocked: false,
      answerStreaming: false,
      _pendingAnswer: "",
      _thinkingSealed: false,
      _thinkingFromDelta: false,
      _thinkingRevealComplete: false,
    });
    await scrollToBottom();

    const feedThinking = (idx: number, chunk: string) => {
      if (!chunk || idx < 0) return;
      const msg = messages.value[idx];
      msg._thinkingFromDelta = true;
      msg.liveThinking = appendStreamBuffer(msg.liveThinking || "", chunk);
      void scrollToBottom();
    };

    try {
      let streamMode: "answer" | "think" = "answer";
      let tagBuffer = "";
      const appendDelta = (delta: string, idx: number) => {
        if (!delta || idx < 0) return;
        let answerPart = "";
        let thinkingPart = "";

        for (const ch of delta) {
          if (tagBuffer) {
            tagBuffer += ch;
            if (ch === ">") {
              const tag = tagBuffer.toLowerCase();
              const isThinkTag = /think|redacted_thinking/.test(tag);
              if (isThinkTag) {
                if (tag.startsWith("</")) {
                  streamMode = "answer";
                  messages.value[idx]._thinkingSealed = true;
                } else {
                  streamMode = "think";
                }
              } else if (streamMode === "think") {
                thinkingPart += tagBuffer;
              } else {
                answerPart += tagBuffer;
              }
              tagBuffer = "";
            }
            continue;
          }

          if (ch === "<") {
            tagBuffer = "<";
            continue;
          }

          if (streamMode === "think") thinkingPart += ch;
          else answerPart += ch;
        }

        if (thinkingPart) feedThinking(idx, thinkingPart);
        if (answerPart) appendAnswerChunk(messages.value[idx], answerPart);
      };

      await sendSessionChatStream(sid, text, {
        onStart() {
          void scrollToBottom();
        },
        onThinkingDelta(delta: string) {
          feedThinking(findAssistantIndex(assistantId), delta);
        },
        onThinkingDone() {
          const idx = findAssistantIndex(assistantId);
          if (idx < 0) return;
          messages.value[idx]._thinkingSealed = true;
        },
        onTrace(trace: unknown) {
          const typedTrace = trace as ReasoningTrace;
          const idx = findAssistantIndex(assistantId);
          if (idx < 0) return;
          const msg = messages.value[idx];
          msg.trace = typedTrace;
          void scrollToBottom();
        },
        onReply(reply: string) {
          if (!reply) return;
          const idx = findAssistantIndex(assistantId);
          if (idx < 0) return;
          const msg = messages.value[idx];
          if (!msg.answerUnlocked) {
            if (reply.length >= (msg._pendingAnswer || "").length) {
              msg._pendingAnswer = reply;
            }
          } else if (reply.length > (msg.content || "").length) {
            msg.content = reply;
            msg.answerStreaming = true;
          }
          void scrollToBottom();
        },
        onDelta(delta: string) {
          if (!delta) return;
          appendDelta(delta, findAssistantIndex(assistantId));
          void scrollToBottom();
        },
        onDone(ev) {
          const done = ev as StreamDoneEvent;
          const idx = findAssistantIndex(assistantId);
          if (idx < 0) return;
          const msg = messages.value[idx];

          const finalReply = done.reply || msg._pendingAnswer || msg.content || "";
          if (finalReply && !msg.answerUnlocked) {
            if (finalReply.length >= (msg._pendingAnswer || "").length) {
              msg._pendingAnswer = finalReply;
            }
          } else if (
            finalReply &&
            msg.answerUnlocked &&
            finalReply.length > (msg.content || "").length
          ) {
            msg.content = finalReply;
            msg.answerStreaming = true;
          }
          msg.trace = done.trace || msg.trace;
          finalizeAssistantMessage(msg, scrollToBottom);
          void scrollToBottom();
        },
        onError(err: Error, ev?) {
          const errEv = ev as StreamErrorEvent | undefined;
          const idx = findAssistantIndex(assistantId);
          const hint = errEv
            ? `请求失败：${errEv.error || err.message} | 类型: ${errEv.error_type || ""} | 请求ID: ${errEv.request_id || ""}`
            : formatNetworkError(err);
          if (idx >= 0) {
            messages.value[idx].content = hint;
            messages.value[idx].streaming = false;
            messages.value[idx]._thinkingSealed = true;
            messages.value[idx]._thinkingRevealComplete = true;
            messages.value[idx].answerUnlocked = true;
            messages.value[idx].answerStreaming = false;
          }
          ElMessage.error(hint);
          logger.error("stream error", { sessionId: sid, err, ev });
        },
      });
      await loadSessions();
    } catch (err) {
      const idx = findAssistantIndex(assistantId);
      const errHint = formatNetworkError(err);
      if (idx >= 0) {
        messages.value[idx].content = errHint;
        messages.value[idx].streaming = false;
        messages.value[idx]._thinkingSealed = true;
        messages.value[idx]._thinkingRevealComplete = true;
        messages.value[idx].answerUnlocked = true;
        messages.value[idx].answerStreaming = false;
      }
      ElMessage.error(errHint);
      setOnline(false);
    } finally {
      loading.value = false;
      const idx = findAssistantIndex(assistantId);
      if (idx >= 0) {
        finalizeAssistantMessage(messages.value[idx], scrollToBottom);
      }
      await scrollToBottom();
    }
  }

  return { send };
}

interface ScrollbarLike {
  wrapRef?: HTMLElement;
}

export function useScrollToBottom(scrollbarRef: Ref<ScrollbarLike | null>) {
  let scrollRaf: number | null = null;

  async function scrollToBottom(): Promise<void> {
    if (scrollRaf != null) return;
    scrollRaf = requestAnimationFrame(async () => {
      scrollRaf = null;
      await nextTick();
      const wrap = scrollbarRef.value?.wrapRef;
      if (wrap) wrap.scrollTop = wrap.scrollHeight;
    });
  }

  return { scrollToBottom };
}
