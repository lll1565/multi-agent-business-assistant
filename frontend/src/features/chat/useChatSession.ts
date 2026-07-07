import { computed, ref, type Ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import {
  createSession,
  deleteSession,
  getSession,
  listSessions,
  updateSession,
} from "../../api/chat";
import { STORAGE_KEY } from "./constants";
import type { ChatMessage, SessionCommand, SessionSummary } from "./types";

interface UseChatSessionOptions {
  messages: Ref<ChatMessage[]>;
  loading: Ref<boolean>;
  scrollToBottom: () => void | Promise<void>;
  normalizeMessage: (m: ChatMessage) => ChatMessage;
}

export function useChatSession({
  messages,
  loading,
  scrollToBottom,
  normalizeMessage,
}: UseChatSessionOptions) {
  const sessions = ref<SessionSummary[]>([]);
  const currentSessionId = ref<string | null>(null);

  const currentTitle = computed(() => {
    const s = sessions.value.find((x) => x.id === currentSessionId.value);
    return s?.title || "多 Agent 对话";
  });

  function previewText(s: SessionSummary): string {
    return s.preview || "暂无消息";
  }

  function formatTime(iso: string | undefined): string {
    if (!iso) return "";
    try {
      const d = new Date(iso);
      return d.toLocaleString("zh-CN", {
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return "";
    }
  }

  async function loadSessions(): Promise<void> {
    try {
      sessions.value = await listSessions();
    } catch {
      sessions.value = [];
    }
  }

  async function onNewChat(): Promise<void> {
    try {
      const session = await createSession();
      sessions.value.unshift(session);
      await selectSession(session.id);
    } catch {
      ElMessage.error("创建会话失败");
    }
  }

  async function selectSession(sessionId: string): Promise<void> {
    if (loading.value) return;
    currentSessionId.value = sessionId;
    localStorage.setItem(STORAGE_KEY, sessionId);
    messages.value = [];
    try {
      const data = await getSession(sessionId);
      messages.value = (data.messages || []).map((m) =>
        normalizeMessage(m as ChatMessage),
      );
      const idx = sessions.value.findIndex((s) => s.id === sessionId);
      if (idx >= 0) sessions.value[idx].title = data.title;
      await scrollToBottom();
    } catch {
      ElMessage.error("加载会话失败");
    }
  }

  async function onSessionCommand(
    cmd: SessionCommand,
    session: SessionSummary,
  ): Promise<void> {
    if (cmd === "rename") {
      const { value } = await ElMessageBox.prompt("会话标题", "重命名", {
        inputValue: session.title,
      }).catch(() => ({ value: null as string | null }));
      if (!value?.trim()) return;
      try {
        await updateSession(session.id, value.trim());
        session.title = value.trim();
        ElMessage.success("已重命名");
      } catch {
        ElMessage.error("重命名失败");
      }
    } else if (cmd === "delete") {
      try {
        await ElMessageBox.confirm("确定删除此会话及全部消息？", "删除会话", {
          type: "warning",
        });
      } catch {
        return;
      }
      try {
        await deleteSession(session.id);
        sessions.value = sessions.value.filter((s) => s.id !== session.id);
        if (currentSessionId.value === session.id) {
          if (sessions.value.length > 0) await selectSession(sessions.value[0].id);
          else await onNewChat();
        }
        ElMessage.success("已删除");
      } catch {
        ElMessage.error("删除失败");
      }
    }
  }

  async function bootstrapSession(): Promise<void> {
    await loadSessions();
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved && sessions.value.some((s) => s.id === saved)) {
      await selectSession(saved);
    } else if (sessions.value.length > 0) {
      await selectSession(sessions.value[0].id);
    } else {
      await onNewChat();
    }
  }

  return {
    sessions,
    currentSessionId,
    currentTitle,
    previewText,
    formatTime,
    loadSessions,
    onNewChat,
    selectSession,
    onSessionCommand,
    bootstrapSession,
  };
}
