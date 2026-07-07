<template>
  <div class="welcome-empty">
    <div class="welcome-icon" aria-hidden="true">
      <el-icon :size="44"><ChatDotRound /></el-icon>
    </div>
    <h2 class="welcome-title">选择示例问题，或输入你的问题</h2>
    <p class="welcome-sub">支持数据库查询、订单列表与 API 文档检索</p>
    <div class="example-chips">
      <button
        v-for="q in examples"
        :key="q"
        type="button"
        class="example-chip"
        @click="$emit('pick', q)"
      >
        {{ q }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ChatDotRound } from "@element-plus/icons-vue";

defineProps({
  examples: { type: Array, default: () => [] },
});

defineEmits(["pick"]);
</script>

<style scoped>
.welcome-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 48px 20px 32px;
  max-width: var(--chat-thread-width, 800px);
  width: 100%;
  min-height: min(520px, calc(100vh - 240px));
  margin: 0 auto;
  justify-content: center;
}

.welcome-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 88px;
  height: 88px;
  border-radius: 24px;
  background: var(--app-accent-soft);
  color: var(--app-accent);
  margin-bottom: 20px;
  flex-shrink: 0;
}

.welcome-title {
  margin: 0 0 8px;
  font-size: 18px;
  font-weight: 600;
  line-height: 1.5;
  color: var(--app-text-primary);
  letter-spacing: normal;
  word-break: keep-all;
  white-space: normal;
}

.welcome-sub {
  margin: 0 0 24px;
  font-size: 14px;
  line-height: 1.6;
  color: var(--app-text-muted);
}

.example-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: center;
  width: 100%;
}

.example-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 36px;
  padding: 8px 16px;
  font-size: 14px;
  line-height: 1.4;
  color: var(--app-accent);
  background: var(--app-bg-surface);
  border: 1px solid var(--app-border-soft);
  border-radius: 999px;
  cursor: pointer;
  transition:
    background 0.2s ease,
    border-color 0.2s ease,
    color 0.2s ease,
    box-shadow 0.2s ease,
    transform 0.15s ease;
  box-shadow: 0 1px 4px rgba(29, 33, 41, 0.06);
  font-family: inherit;
}

.example-chip:hover {
  background: var(--app-accent-soft);
  border-color: var(--app-accent);
  color: var(--app-accent);
  box-shadow: 0 4px 12px rgba(78, 110, 242, 0.15);
  transform: translateY(-1px);
}

.example-chip:active {
  transform: translateY(0);
  box-shadow: 0 1px 4px rgba(29, 33, 41, 0.08);
}

.example-chip:focus-visible {
  outline: 2px solid var(--app-accent);
  outline-offset: 2px;
}
</style>
