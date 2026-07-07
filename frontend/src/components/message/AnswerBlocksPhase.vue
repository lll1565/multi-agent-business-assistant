<template>
  <TransitionGroup
    name="block-stagger"
    tag="div"
    class="answer-blocks"
    appear
  >
    <div
      v-for="(block, i) in blocks"
      :key="blockStableKey(block, i)"
      class="block-stagger-item"
    >
      <AnswerProseBlock
        v-if="block.type === BLOCK_TYPES.TEXT && (block.content || '').trim()"
        :content="block.content"
      />
      <AnswerTableCard
        v-else-if="block.type === BLOCK_TYPES.TABLE"
        :block="block"
      />
      <AnswerCodeBlock
        v-else-if="block.type === BLOCK_TYPES.CODE"
        :content="block.content"
        :language="block.language"
      />
    </div>
  </TransitionGroup>
</template>

<script setup>
import { BLOCK_TYPES, blockStableKey } from "../../modules/message-blocks";
import AnswerCodeBlock from "./AnswerCodeBlock.vue";
import AnswerProseBlock from "./AnswerProseBlock.vue";
import AnswerTableCard from "./AnswerTableCard.vue";

defineProps({
  blocks: { type: Array, default: () => [] },
});
</script>

<style scoped>
.answer-blocks {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.block-stagger-item {
  display: block;
}
</style>
