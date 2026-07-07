<template>
  <article v-if="hasContent || streaming" class="message-content answer-surface">
    <div class="answer-body">
      <Transition name="stream-phase" mode="out-in">
        <AnswerStreamPhase
          v-if="streaming"
          key="stream"
          :content="content"
          :streaming="streaming"
          @scroll="$emit('scroll')"
          @done="onStreamDone"
        />
        <AnswerBlocksPhase
          v-else
          key="blocks"
          :blocks="blocks"
        />
      </Transition>
    </div>
  </article>
</template>

<script setup>
import { computed, watch } from "vue";
import AnswerBlocksPhase from "./message/AnswerBlocksPhase.vue";
import AnswerStreamPhase from "./message/AnswerStreamPhase.vue";
import {
  blockHasContent,
  parseMessageBlocks,
} from "../modules/message-blocks";

const props = defineProps({
  content: { type: String, default: "" },
  streaming: { type: Boolean, default: false },
});

const emit = defineEmits(["scroll", "done"]);

const blocks = computed(() => parseMessageBlocks(props.content));

const hasContent = computed(() =>
  blocks.value.some((b) => blockHasContent(b))
);

function onStreamDone() {
  emit("done");
}

watch(
  () => props.streaming,
  (s, was) => {
    if (was && !s) emit("done");
  }
);
</script>
