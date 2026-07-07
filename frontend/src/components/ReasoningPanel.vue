<template>
  <div v-if="showPanel" class="reasoning-ds">
    <button
      type="button"
      class="reasoning-toggle"
      :aria-expanded="bodyOpen"
      @click="onHeaderClick"
    >
      <span class="reasoning-title">{{ headerLabel }}</span>
      <el-icon class="chevron" :class="{ expanded: bodyOpen }"><ArrowDown /></el-icon>
    </button>

    <div class="reasoning-collapse" :class="{ expanded: bodyOpen }">
      <div ref="bodyRef" class="reasoning-body" @scroll="onBodyScroll">
        <ThinkingStream
          v-if="useStream"
          :text="liveThinking"
          :sealed="streamSealed"
          @tick="onThinkingTick"
          @done="onThinkingStreamDone"
        />
        <div v-else-if="displayText" class="reasoning-static">{{ displayText }}</div>
        <p v-else-if="isActive" class="reasoning-hint">{{ statusHint }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, ref, watch } from "vue";
import { ArrowDown } from "@element-plus/icons-vue";
import ThinkingStream from "./ThinkingStream.vue";
import { buildThinkingDisplayText } from "../utils/traceNarrative";
import { useStickToBottom } from "../composables/useStickToBottom";

const props = defineProps({
  trace: { type: Object, default: null },
  streaming: { type: Boolean, default: false },
  outputting: { type: Boolean, default: false },
  historical: { type: Boolean, default: false },
  liveThinking: { type: String, default: "" },
  thinkingSealed: { type: Boolean, default: false },
});

const emit = defineEmits(["scroll", "thinking-reveal-done"]);

const userExpanded = ref(true);
const thinkingRevealDone = ref(false);
const thinkingMs = ref(0);
const liveSec = ref(0);
let thinkStartedAt = 0;
let liveTimer = null;

const bodyRef = ref(null);
const { onScroll: onBodyScroll, scrollToBottomIfStuck } = useStickToBottom(bodyRef);

const liveThinking = computed(() => props.liveThinking || "");

function onThinkingTick() {
  nextTick(() => {
    scrollToBottomIfStuck();
    emit("scroll");
  });
}

watch(liveThinking, () => {
  nextTick(() => scrollToBottomIfStuck());
});

const displayText = computed(() => {
  const live = liveThinking.value.trim();
  if (live) return live;
  return buildThinkingDisplayText(props.trace);
});

const isActive = computed(
  () => !props.historical && (props.outputting || props.streaming)
);

/** 当前轮：打字机展示思考（SSE 结束仍继续逐字追平队列） */
const useStream = computed(() => {
  if (props.historical || thinkingRevealDone.value) return false;
  if (props.outputting || props.streaming) return true;
  return props.thinkingSealed && !!liveThinking.value.trim();
});

const streamSealed = computed(
  () => props.thinkingSealed && !props.streaming
);

const bodyOpen = computed(() => {
  if (props.outputting || props.streaming) return true;
  if (useStream.value) return true;
  // 历史消息默认展开；用户可手动收起
  if (props.historical) return userExpanded.value;
  return userExpanded.value;
});

const showPanel = computed(() => {
  if (!props.historical && (props.streaming || props.outputting)) return true;
  return !!displayText.value.trim();
});

const elapsedSec = computed(() => {
  if (thinkingMs.value > 0) return Math.max(1, Math.round(thinkingMs.value / 1000));
  if (liveSec.value > 0) return liveSec.value;
  const len = displayText.value.length;
  return len > 0 ? Math.max(1, Math.ceil(len / 100)) : 1;
});

const headerLabel = computed(() => {
  if (useStream.value && !props.thinkingSealed) {
    return liveSec.value > 0 ? `思考中（${liveSec.value} 秒）` : "思考中…";
  }
  return `已思考（用时 ${elapsedSec.value} 秒）`;
});

watch(
  () => props.streaming,
  (streaming, was) => {
    if (streaming) {
      thinkingRevealDone.value = false;
      thinkingMs.value = 0;
      liveSec.value = 0;
      userExpanded.value = true;
      thinkStartedAt = Date.now();
      startLiveTimer();
      return;
    }
    if (was) stopLiveTimer();
  }
);

watch(
  () => props.thinkingSealed,
  (sealed) => {
    if (!sealed || props.historical || thinkingRevealDone.value) return;
    if (!liveThinking.value.trim()) finishThinkingPhase();
  }
);

function onThinkingStreamDone() {
  if (!props.thinkingSealed || props.historical || thinkingRevealDone.value) return;
  finishThinkingPhase();
}

watch(
  () => props.historical,
  (hist) => {
    if (!hist) return;
    stopLiveTimer();
    thinkingRevealDone.value = true;
    // 刷新加载的历史消息：有思考内容时默认展开（与流式结束时一致）
    userExpanded.value = !!displayText.value.trim();
    if (!thinkingMs.value && displayText.value) {
      thinkingMs.value = Math.max(500, Math.min(12000, displayText.value.length * 25));
    }
  },
  { immediate: true }
);

function startLiveTimer() {
  stopLiveTimer();
  liveTimer = setInterval(() => {
    if (thinkStartedAt) {
      liveSec.value = Math.max(1, Math.round((Date.now() - thinkStartedAt) / 1000));
    }
  }, 500);
}

function stopLiveTimer() {
  if (liveTimer) {
    clearInterval(liveTimer);
    liveTimer = null;
  }
}

function finishThinkingPhase() {
  if (thinkingRevealDone.value) return;
  thinkingRevealDone.value = true;
  if (thinkStartedAt && !thinkingMs.value) {
    thinkingMs.value = Math.max(500, Date.now() - thinkStartedAt);
  }
  stopLiveTimer();
  emit("thinking-reveal-done");
}

function onHeaderClick() {
  if (props.outputting || props.streaming) return;
  userExpanded.value = !userExpanded.value;
}

const statusHint = computed(() => {
  const steps = props.trace?.steps || [];
  const last = steps[steps.length - 1];
  if (!last) return "正在分析问题…";
  if (last.type === "delegate") return last.title || "正在委派子 Agent…";
  if (last.type === "tool" || last.type === "sub_tool") return last.title || "正在调用工具…";
  return "正在分析问题…";
});

onBeforeUnmount(stopLiveTimer);
</script>

<style scoped>
.reasoning-ds {
  margin-bottom: 6px;
}

.reasoning-toggle {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 0;
  margin: 0;
  border: none;
  background: none;
  cursor: pointer;
  font-size: 13px;
  color: var(--app-text-thinking);
  line-height: 1.5;
}

.reasoning-toggle:hover .reasoning-title {
  color: #5c5c5c;
}

.chevron {
  font-size: 14px;
  color: var(--app-text-muted);
  transition: transform 0.2s ease;
  transform: rotate(-90deg);
}

.chevron.expanded {
  transform: rotate(0deg);
}

.reasoning-collapse {
  display: grid;
  grid-template-rows: 0fr;
  transition: grid-template-rows 0.15s ease;
}

.reasoning-collapse.expanded {
  grid-template-rows: 1fr;
  margin-top: 6px;
}

.reasoning-body {
  overflow: hidden;
  min-height: 0;
  padding: 4px 0 4px 14px;
  border-left: 2px solid var(--app-border-soft);
  /* 与 DeepSeek 一致：思考区随内容增高，由外层消息列表滚动，不设内部滑块 */
}

.reasoning-body :deep(.thinking-stream) {
  font-size: 14px;
  line-height: 1.75;
  color: var(--app-text-thinking);
}

.reasoning-static {
  font-size: 14px;
  line-height: 1.75;
  color: var(--app-text-thinking);
  white-space: pre-wrap;
  word-break: break-word;
}

.reasoning-hint {
  margin: 0;
  font-size: 14px;
  color: var(--app-text-muted);
}
</style>
