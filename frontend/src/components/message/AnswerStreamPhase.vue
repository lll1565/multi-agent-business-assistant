<template>
  <div class="answer-prose is-streaming">
    <StreamText
      :text="content"
      :streaming="streaming"
      tag="div"
      class="stream-inner"
      :ms-per-char="ANSWER_PACE.msPerChar"
      :max-chars-per-frame="ANSWER_PACE.maxPerFrame"
      @tick="$emit('scroll')"
      @done="$emit('done')"
    />
  </div>
</template>

<script setup>
import StreamText from "../StreamText.vue";
import { ANSWER_PACE } from "../../constants/streamPace";

defineProps({
  content: { type: String, default: "" },
  streaming: { type: Boolean, default: true },
});

defineEmits(["scroll", "done"]);
</script>

<style scoped>
.stream-inner :deep(.stream-text) {
  display: block;
}
</style>
