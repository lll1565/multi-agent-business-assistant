/** API envelope and shared HTTP types. */

export interface ApiResponse<T = unknown> {
  code: number;
  message: string;
  data: T | null;
  request_id?: string | null;
}

export interface ApiEnvelopeError extends Error {
  code?: number;
  response?: { data?: ApiResponse };
}

export interface HealthInfo {
  status: string;
  service: string;
  model?: string | null;
  log_file?: string | null;
  docs_url?: string;
}

export interface SessionDetail {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  preview?: string | null;
  messages?: Array<{
    id: string;
    role: string;
    content: string;
    created_at: string;
    trace?: unknown;
  }>;
}

export interface ChatResult {
  reply: string;
  success: boolean;
  error?: string | null;
  error_type?: string | null;
  request_id?: string | null;
  trace?: unknown;
  user_message?: Record<string, unknown> | null;
  assistant_message?: Record<string, unknown> | null;
}

export interface SessionSummary {
  id: string;
  title: string;
  preview?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface SseEvent {
  type: string;
  reply?: string;
  trace?: unknown;
  delta?: string;
  error?: string;
  error_type?: string;
  success?: boolean;
  request_id?: string;
  [key: string]: unknown;
}

export interface StreamCallbacks {
  onStart?: (ev: SseEvent) => void;
  onTrace?: (trace: unknown) => void;
  onReply?: (reply: string) => void;
  onDelta?: (delta: string) => void;
  onThinkingDelta?: (delta: string) => void;
  onThinkingDone?: () => void;
  onDone?: (ev: SseEvent) => void;
  onError?: (err: Error, ev?: SseEvent) => void;
}
