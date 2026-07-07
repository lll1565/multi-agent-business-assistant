<template>
  <div
    class="answer-prose text-block"
    :class="{ 'is-api-doc': isApiDoc }"
    v-html="html"
  />
</template>

<script setup>
import { computed } from "vue";
import { renderMarkdownHtml } from "../../modules/markdown";

const props = defineProps({
  content: { type: String, default: "" },
});

const html = computed(() => renderMarkdownHtml(props.content));

const isApiDoc = computed(() =>
  /##\s+API\s+接口|###\s+请求参数/.test(props.content || "")
);
</script>
