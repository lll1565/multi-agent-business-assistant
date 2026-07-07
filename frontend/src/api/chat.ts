import axios, {type AxiosError, type InternalAxiosRequestConfig} from "axios";
import {logger} from "../utils/logger";
import type {
    ApiEnvelopeError,
    ApiResponse,
    ChatResult,
    HealthInfo,
    SessionDetail,
    SessionSummary,
    SseEvent,
    StreamCallbacks,
} from "./types";

interface RequestMetadata {
  requestId: string;
  start: number;
}

type ConfigWithMetadata = InternalAxiosRequestConfig & {
  metadata?: RequestMetadata;
};

function isApiEnvelope(payload: unknown): payload is ApiResponse {
  return (
    typeof payload === "object" &&
    payload !== null &&
    typeof (payload as ApiResponse).code === "number" &&
    Object.prototype.hasOwnProperty.call(payload, "data")
  );
}

function unwrapEnvelope<T>(payload: unknown): T {
  if (isApiEnvelope(payload)) {
    if (payload.code !== 0) {
      const err = new Error(payload.message || "请求失败") as ApiEnvelopeError;
      err.code = payload.code;
      err.response = { data: payload };
      throw err;
    }
    return payload.data as T;
  }
  return payload as T;
}

const API_KEY = (import.meta.env.VITE_API_KEY as string | undefined)?.trim();

function withApiKey(headers: Record<string, string>): Record<string, string> {
  if (API_KEY) {
    headers["X-API-Key"] = API_KEY;
  }
  return headers;
}

const http = axios.create({
  baseURL: "/api",
  timeout: 300000,
});

http.interceptors.request.use((config) => {
  const cfg = config as ConfigWithMetadata;
  const id = `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`;
  cfg.headers["X-Request-Id"] = id;
  withApiKey(cfg.headers as Record<string, string>);
  cfg.metadata = { requestId: id, start: performance.now() };
  logger.info("HTTP →", cfg.method?.toUpperCase(), cfg.url, {
    requestId: id,
    data: cfg.data,
  });
  return cfg;
});

http.interceptors.response.use(
  (response) => {
    const cfg = response.config as ConfigWithMetadata;
    const meta = cfg.metadata || { requestId: "-", start: 0 };
    const ms = Math.round(performance.now() - meta.start);
    response.data = unwrapEnvelope(response.data);
    const data = response.data as ChatResult | undefined;
    logger.info("HTTP ←", response.status, cfg.url, {
      requestId: meta.requestId,
      ms,
      success: data?.success,
      error: data?.error,
      replyLen: data?.reply?.length,
    });
    return response;
  },
  (error: AxiosError<ApiResponse>) => {
    const cfg = (error.config || {}) as ConfigWithMetadata;
    const meta = cfg.metadata || { requestId: "-", start: 0 };
    const ms = Math.round(performance.now() - meta.start);
    const envelope = error.response?.data;
    const detail =
      (envelope && envelope.message) ||
      (envelope as { error?: string } | undefined)?.error ||
      (envelope as { detail?: string } | undefined)?.detail ||
      error.message;
    logger.error("HTTP ✗", cfg.method?.toUpperCase(), cfg.url, {
      requestId: meta.requestId,
      ms,
      status: error.response?.status,
      detail,
      data: error.response?.data,
    });
    return Promise.reject(error);
  },
);

export async function checkHealth(): Promise<HealthInfo> {
  const { data } = await http.get<HealthInfo>("/health");
  return data;
}

export async function listSessions(): Promise<SessionSummary[]> {
  const { data } = await http.get<{ sessions: SessionSummary[] }>("/sessions");
  return data.sessions;
}

export async function createSession(title = "新对话"): Promise<SessionDetail> {
  const { data } = await http.post<SessionDetail>("/sessions", { title });
  return data;
}

export async function getSession(sessionId: string): Promise<SessionDetail> {
  const { data } = await http.get<SessionDetail>(`/sessions/${sessionId}`);
  return data;
}

export async function updateSession(
  sessionId: string,
  title: string,
): Promise<SessionDetail> {
  const { data } = await http.patch<SessionDetail>(`/sessions/${sessionId}`, {
    title,
  });
  return data;
}

export async function deleteSession(
  sessionId: string,
): Promise<{ ok: boolean }> {
  const { data } = await http.delete<{ ok: boolean }>(`/sessions/${sessionId}`);
  return data;
}

export async function sendSessionChat(
  sessionId: string,
  message: string,
): Promise<ChatResult> {
  logger.info("sendSessionChat", {
    sessionId,
    messagePreview: message.slice(0, 80),
  });
  const { data } = await http.post<ChatResult>(`/sessions/${sessionId}/chat`, {
    message,
  });
  if (!data.success && data.error) {
    logger.warn("chat business error", { sessionId, error: data.error });
  }
  return data;
}

/**
 * Stream chat via SSE. callbacks: onStart, onTrace, onReply, onDelta, onDone, onError
 */
export async function sendSessionChatStream(
  sessionId: string,
  message: string,
  callbacks: StreamCallbacks = {},
): Promise<void> {
  const requestId = `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`;
  logger.info("sendSessionChatStream", {
    sessionId,
    requestId,
    messagePreview: message.slice(0, 80),
  });

  const res = await fetch(`/api/sessions/${sessionId}/chat/stream`, {
    method: "POST",
    headers: withApiKey({
      "Content-Type": "application/json",
      "X-Request-Id": requestId,
    }),
    body: JSON.stringify({ message }),
  });

  if (!res.ok) {
    let text = await res.text();
    try {
      const parsed = JSON.parse(text) as ApiResponse;
      if (parsed.message) text = parsed.message;
    } catch {
      /* keep raw text */
    }
    const err = new Error(text || `HTTP ${res.status}`) as Error & {
      status?: number;
    };
    err.status = res.status;
    callbacks.onError?.(err);
    throw err;
  }

  const reader = res.body?.getReader();
  if (!reader) {
    throw new Error("流式响应不可用");
  }

  const decoder = new TextDecoder();
  let buffer = "";

  const flushEvent = (line: string): void => {
    if (!line.startsWith("data:")) return;
    const raw = line.slice(5).trim();
    if (!raw) return;
    let ev: SseEvent;
    try {
      ev = JSON.parse(raw) as SseEvent;
    } catch {
      logger.warn("SSE parse error", raw);
      return;
    }
    logger.debug("SSE event", ev.type);
    switch (ev.type) {
      case "started":
        callbacks.onStart?.(ev);
        break;
      case "trace":
        callbacks.onTrace?.(ev.trace);
        break;
      case "reply":
        callbacks.onReply?.(ev.reply ?? "");
        break;
      case "reply_delta":
        callbacks.onDelta?.(ev.delta ?? "");
        break;
      case "thinking_delta":
        callbacks.onThinkingDelta?.(ev.delta ?? "");
        break;
      case "thinking_done":
        callbacks.onThinkingDone?.();
        break;
      case "done":
        callbacks.onDone?.(ev);
        break;
      case "error":
        callbacks.onError?.(new Error(ev.error || "未知错误"), ev);
        break;
      default:
        break;
    }
  };

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop() || "";
    for (const block of parts) {
      const line = block.split("\n").find((l) => l.startsWith("data:"));
      if (line) flushEvent(line);
    }
  }
  if (buffer.trim()) {
    const line = buffer.split("\n").find((l) => l.startsWith("data:"));
    if (line) flushEvent(line);
  }
}
