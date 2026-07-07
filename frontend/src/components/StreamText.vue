<template>
  <component :is="tag" class="stream-text" :class="{ streaming }">
    {{ displayed }}<span v-if="showCaret" class="caret" />
  </component>
</template>

<script setup>
import { computed, onMounted, toRef, watch } from "vue";
import { useTypewriter } from "../composables/useTypewriter";

const props = defineProps({
  text: { type: String, default: "" },
  streaming: { type: Boolean, default: false },
  tag: { type: String, default: "span" },
  /** ~35 chars/s at 28ms/char */
  msPerChar: { type: Number, default: 28 },
  maxCharsPerFrame: { type: Number, default: 2 },
});

const emit = defineEmits(["tick", "done"]);

const textRef = toRef(props, "text");
const { displayed, flush, ensureAnim } = useTypewriter(() => textRef.value, {
  msPerChar: props.msPerChar,
  maxCharsPerFrame: props.maxCharsPerFrame,
});

const targetLen = computed(() => props.text?.length || 0);

const showCaret = computed(() => displayed.value.length < targetLen.value);

let doneEmitted = false;

function resetDone() {
  doneEmitted = false;
}

function maybeDone() {
  if (doneEmitted) return;
  if (displayed.value.length >= targetLen.value) {
    doneEmitted = true;
    emit("done");
  }
}

watch(
  () => props.text,
  (next, prev) => {
    if (
      (next?.length || 0) > (prev?.length || 0) &&
      (next?.length || 0) > displayed.value.length
    ) {
      resetDone();
    }
    ensureAnim();
  },
  { immediate: true }
);

onMounted(() => ensureAnim());

watch(displayed, () => {
  emit("tick");
  maybeDone();
});

watch(targetLen, () => {
  ensureAnim();
  maybeDone();
});

watch(
  () => props.streaming,
  (s, was) => {
    if (s) {
      ensureAnim();
      return;
    }
    if (was && displayed.value.length >= targetLen.value) {
      flush();
      maybeDone();
    }
  }
);
</script>

<style scoped>
.stream-text {
  display: block;
  white-space: pre-wrap;
  word-break: break-word;
  overflow-wrap: anywhere;
}

.caret {
  display: inline-block;
  width: 2px;
  height: 1.05em;
  margin-left: 1px;
  vertical-align: text-bottom;
  background: #4e6ef2;
  border-radius: 1px;
  animation: caret-blink 1.05s step-end infinite;
}

@keyframes caret-blink {
  50% {
    opacity: 0;
  }
}
</style>
