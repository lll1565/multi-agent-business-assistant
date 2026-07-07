<template>
  <div class="app-shell" :class="{ 'is-sidebar-collapsed': sidebarCollapsed }">
    <SessionSidebar
      :sessions="sessions"
      :current-session-id="currentSessionId ?? undefined"
      :preview-text="previewText"
      @toggle-sidebar="toggleSidebar"
      @new-chat="onNewChat"
      @select-session="selectSession"
      @session-command="onSessionCommand"
    />

    <div class="main">
      <header class="header">
        <div class="header-inner">
          <div class="header-start">
            <div v-if="sidebarCollapsed" class="header-nav-tools">
              <button
                type="button"
                class="sidebar-toggle-btn is-light"
                title="展开侧栏"
                aria-label="展开侧栏"
                @click="toggleSidebar"
              >
                <el-icon :size="18"><Expand /></el-icon>
              </button>
              <span class="header-mark" aria-hidden="true">
                <el-icon :size="20"><ChatDotRound /></el-icon>
              </span>
            </div>
            <span class="title">{{ currentTitle }}</span>
          </div>
          <div class="header-actions">
            <ThemeToggle />
            <el-tag
              class="status-tag"
              :type="online ? 'success' : 'danger'"
              size="small"
              round
              effect="light"
            >
              {{ online ? "服务在线" : "服务离线" }}
            </el-tag>
          </div>
        </div>
      </header>

      <main class="chat-panel">
        <el-scrollbar ref="scrollbarRef" class="messages-scroll">
          <div class="chat-thread">
            <WelcomeEmpty
              v-if="messages.length === 0 && !loading"
              :examples="CHAT_EXAMPLES"
              @pick="useExample"
            />

            <div
              v-for="msg in messages"
              :key="msg.id || msg.created_at + msg.role"
              class="message-row"
              :class="msg.role"
            >
              <el-avatar
                :size="40"
                class="message-avatar"
                :class="msg.role === 'user' ? 'avatar-user' : 'avatar-bot'"
                :icon="msg.role === 'user' ? UserFilled : Service"
              />
              <div class="bubble">
                <div class="meta">
                  <span>{{ msg.role === "user" ? "你" : "助手" }}</span>
                  <span v-if="msg.created_at" class="time">{{ formatTime(msg.created_at) }}</span>
                </div>

                <ReasoningPanel
                  v-if="msg.role === 'assistant'"
                  :trace="msg.trace ?? undefined"
                  :streaming="!!msg.streaming"
                  :outputting="!!msg.streaming || !!msg.answerStreaming"
                  :historical="isHistoricalMessage(msg)"
                  :live-thinking="msg.liveThinking || ''"
                  :thinking-sealed="!!msg._thinkingSealed"
                  @scroll="scrollToBottom"
                  @thinking-reveal-done="() => handleThinkingDone(msg)"
                />
                <MessageContent
                  v-if="msg.role !== 'assistant' || msg.answerUnlocked"
                  :content="msg.content || ''"
                  :streaming="!!msg.answerStreaming"
                  @scroll="scrollToBottom"
                  @done="() => onAnswerRevealDone(msg)"
                />
              </div>
            </div>
          </div>
        </el-scrollbar>

        <ChatInputBar
          v-model="input"
          placeholder="输入问题，查询结果将以表格展示。"
          :disabled="loading || !currentSessionId"
          :loading="loading"
          :send-disabled="!input.trim() || !currentSessionId"
          @send="send"
        />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { ChatDotRound, Expand, Service, UserFilled } from "@element-plus/icons-vue";
import { useSidebarCollapse } from "../../composables/useSidebarCollapse.js";
import SessionSidebar from "../../components/sidebar/SessionSidebar.vue";
import ChatInputBar from "../../components/chat/ChatInputBar.vue";
import WelcomeEmpty from "../../components/chat/WelcomeEmpty.vue";
import MessageContent from "../../components/MessageContent.vue";
import ReasoningPanel from "../../components/ReasoningPanel.vue";
import ThemeToggle from "../../components/theme/ThemeToggle.vue";
import { checkHealth } from "../../api/chat";
import { CHAT_EXAMPLES } from "./constants";
import { useChatSession } from "./useChatSession";
import { useChatSend, useScrollToBottom } from "./useChatSend";
import { useMessageState } from "./useMessageState";
import type { ChatMessage } from "./types";

const { collapsed: sidebarCollapsed, toggle: toggleSidebar } = useSidebarCollapse();

const messages = ref<ChatMessage[]>([]);
const input = ref("");
const loading = ref(false);
const online = ref(false);
const scrollbarRef = ref<{ wrapRef?: HTMLElement } | null>(null);

const messageState = useMessageState();
const { isHistoricalMessage, normalizeMessage, onThinkingRevealDone, onAnswerRevealDone } =
  messageState;
const { scrollToBottom } = useScrollToBottom(scrollbarRef);

const {
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
} = useChatSession({ messages, loading, scrollToBottom, normalizeMessage });

const { send } = useChatSend({
  messages,
  input,
  loading,
  currentSessionId,
  loadSessions,
  scrollToBottom,
  messageState,
  setOnline: (v: boolean) => {
    online.value = v;
  },
});

function handleThinkingDone(msg: ChatMessage): void {
  onThinkingRevealDone(msg, scrollToBottom);
}

function useExample(q: string): void {
  input.value = q;
  void send();
}

onMounted(async () => {
  try {
    await checkHealth();
    online.value = true;
  } catch {
    online.value = false;
  }
  await bootstrapSession();
});
</script>

<style src="./chat-page.css"></style>
