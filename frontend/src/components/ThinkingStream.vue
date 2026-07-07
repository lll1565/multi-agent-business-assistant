<template>
  <div class="thinking-stream">
    <span class="thinking-text">{{ visible }}</span
    ><span v-if="showCaret" class="caret" />
  </div>
</template>

<script setup>
import { computed, toRef, watch } from "vue";
import { usePacedSource } from "../composables/usePacedSource";
import { THINKING_PACE } from "../constants/streamPace";

const props = defineProps({
  text: { type: String, default: "" },
  /** SSE finished; stop accepting new source but keep revealing queue */
  sealed: { type: Boolean, default: false },
  msPerChar: { type: Number, default: THINKING_PACE.msPerChar },
  maxPerFrame: { type: Number, default: THINKING_PACE.maxPerFrame },
});

const emit = defineEmits(["tick", "done"]);

const textRef = toRef(props, "text");
const { visible, pending, seal, onDrained } = usePacedSource(textRef, {
  msPerChar: props.msPerChar,
  maxPerFrame: props.maxPerFrame,
  followLatest: THINKING_PACE.followLatest,
  catchUpThreshold: THINKING_PACE.catchUpThreshold,
  catchUpMaxPerFrame: THINKING_PACE.catchUpMaxPerFrame,
  catchUpMinMsPerChar: THINKING_PACE.catchUpMinMsPerChar,
});

const showCaret = computed(() => pending.value);

watch(visible, () => emit("tick"));

watch(
  () => props.sealed,
  (s) => {
    if (s) seal();
  },
  { immediate: true }
);

let doneEmitted = false;
onDrained(() => {
  if (!props.sealed) return;
  if (doneEmitted) return;
  doneEmitted = true;
  emit("done");
});

watch(
  () => props.text,
  () => {
    doneEmitted = false;
  }
);
</script>

<style scoped>
.thinking-stream {
  display: block;
  white-space: pre-wrap;
  word-break: break-word;
  overflow-wrap: anywhere;
  font-size: 13px;
  line-height: 1.75;
  color: #8b8b8b;
}

.caret {
  display: inline-block;
  width: 2px;
  height: 1.05em;
  margin-left: 1px;
  vertical-align: text-bottom;
  background: #8b8b8b;
  border-radius: 1px;
  animation: caret-blink 1s step-end infinite;
}

@keyframes caret-blink {
  50% {
    opacity: 0;
  }
}
</style>
