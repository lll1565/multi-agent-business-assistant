/** Chat feature types — shared by composables and ChatPage. */

export interface ReasoningStep {
  type: string;
  title: string;
  detail?: string;
  agent?: string;
}

export interface ReasoningTrace {
  agents_used: string[];
  agent_labels: string[];
  steps: ReasoningStep[];
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
  trace?: ReasoningTrace | null;
  liveThinking?: string;
  streaming?: boolean;
  answerUnlocked?: boolean;
  answerStreaming?: boolean;
  _pendingAnswer?: string;
  _thinkingSealed?: boolean;
  _thinkingFromDelta?: boolean;
  _thinkingRevealComplete?: boolean;
}

export interface SessionSummary {
  id: string;
  title: string;
  preview?: string | null;
  created_at?: string;
  updated_at?: string;
}

export type SessionCommand = "rename" | "delete";

export interface StreamDoneEvent {
  reply?: string;
  trace?: ReasoningTrace;
  request_id?: string;
  success?: boolean;
}

export interface StreamErrorEvent {
  error?: string;
  error_type?: string;
  request_id?: string;
}
