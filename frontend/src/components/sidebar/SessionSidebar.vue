<template>
  <aside class="sidebar">
    <div class="sidebar-brand">
      <div class="brand-lockup">
        <el-icon :size="20"><ChatDotRound /></el-icon>
        <span class="brand-text">多 Agent</span>
      </div>
      <button
        type="button"
        class="sidebar-toggle-btn"
        title="收起侧栏"
        aria-label="收起侧栏"
        @click="$emit('toggle-sidebar')"
      >
        <el-icon :size="18"><Fold /></el-icon>
      </button>
    </div>
    <div class="sidebar-top">
      <el-button type="primary" class="new-chat-btn" round @click="$emit('new-chat')">
        <el-icon><Plus /></el-icon>
        新对话
      </el-button>
    </div>

    <el-scrollbar class="session-list">
      <div
        v-for="s in sessions"
        :key="s.id"
        class="session-item"
        :class="{ active: s.id === currentSessionId }"
        @click="$emit('select-session', s.id)"
      >
        <el-icon class="session-icon"><ChatLineRound /></el-icon>
        <div class="session-info">
          <div class="session-title">{{ s.title }}</div>
          <div class="session-preview">{{ previewText(s) }}</div>
        </div>
        <el-dropdown trigger="click" @command="(cmd) => $emit('session-command', cmd, s)">
          <el-button class="session-more" text :icon="MoreFilled" @click.stop />
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="rename">重命名</el-dropdown-item>
              <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
      <el-empty v-if="sessions.length === 0" description="暂无会话" :image-size="56" />
    </el-scrollbar>
  </aside>
</template>

<script setup>
import { ChatDotRound, ChatLineRound, Fold, MoreFilled, Plus } from "@element-plus/icons-vue";

defineProps({
  sessions: { type: Array, required: true },
  currentSessionId: { type: String, default: null },
  previewText: { type: Function, required: true },
});

defineEmits(["toggle-sidebar", "new-chat", "select-session", "session-command"]);
</script>
