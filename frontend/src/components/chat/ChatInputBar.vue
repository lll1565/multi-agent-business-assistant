<template>
  <footer class="chat-input-bar">
    <div class="input-shell">
      <el-input
        :model-value="modelValue"
        type="textarea"
        :autosize="{ minRows: 1, maxRows: 4 }"
        :placeholder="placeholder"
        :disabled="disabled"
        resize="none"
        class="chat-textarea"
        @update:model-value="$emit('update:modelValue', $event)"
        @keydown.enter.exact.prevent="$emit('send')"
      />
      <el-button
        type="primary"
        circle
        class="send-btn"
        :loading="loading"
        :disabled="sendDisabled"
        aria-label="发送"
        @click="$emit('send')"
      >
        <el-icon v-if="!loading" :size="18"><Promotion /></el-icon>
      </el-button>
    </div>
  </footer>
</template>

<script setup>
import { Promotion } from "@element-plus/icons-vue";

defineProps({
  modelValue: { type: String, default: "" },
  placeholder: { type: String, default: "" },
  disabled: { type: Boolean, default: false },
  loading: { type: Boolean, default: false },
  sendDisabled: { type: Boolean, default: true },
});

defineEmits(["update:modelValue", "send"]);
</script>

<style scoped>
.chat-input-bar {
  flex-shrink: 0;
  padding: 12px var(--chat-gutter-x, 24px) 20px;
  background: var(--app-bg-page);
  border-top: 1px solid var(--app-border);
}

.input-shell {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  max-width: var(--chat-thread-width, 800px);
  margin: 0 auto;
  box-sizing: border-box;
  padding: 8px 10px 8px 16px;
  background: var(--app-bg-input);
  border: 1px solid var(--app-border-soft);
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(29, 33, 41, 0.06);
  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease;
}

.input-shell:focus-within {
  border-color: var(--app-accent);
  box-shadow: 0 0 0 3px var(--app-accent-soft);
}

.chat-textarea {
  flex: 1;
  min-width: 0;
}

.chat-textarea :deep(.el-textarea__inner) {
  box-shadow: none !important;
  background: transparent !important;
  border: none !important;
  padding: 6px 0 !important;
  font-size: 15px;
  line-height: 1.5;
  color: var(--app-text-primary);
  resize: none;
}

.chat-textarea :deep(.el-textarea__inner::placeholder) {
  color: var(--app-text-muted);
}

.send-btn {
  flex-shrink: 0;
  width: 40px !important;
  height: 40px !important;
  margin: 0;
  padding: 0 !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
}

.send-btn :deep(.el-icon) {
  margin: 0;
}
</style>
