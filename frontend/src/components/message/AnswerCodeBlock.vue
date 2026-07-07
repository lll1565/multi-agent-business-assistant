<template>
  <el-card class="answer-code-shell" shadow="never">
    <template #header>
      <div class="code-head">
        <span class="answer-code-label">{{ language || "code" }}</span>
        <el-button text size="small" class="code-copy" @click="onCopy">
          <el-icon><DocumentCopy /></el-icon>
          复制
        </el-button>
      </div>
    </template>
    <pre class="answer-code-pre"><code>{{ content }}</code></pre>
  </el-card>
</template>

<script setup>
import { DocumentCopy } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import { copyTextToClipboard } from "../../modules/table-export";

const props = defineProps({
  content: { type: String, default: "" },
  language: { type: String, default: "code" },
});

async function onCopy() {
  if (!props.content) return;
  try {
    await copyTextToClipboard(props.content);
    ElMessage.success("已复制代码");
  } catch {
    ElMessage.error("复制失败");
  }
}
</script>

<style scoped>
.code-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.code-copy {
  color: var(--app-text-muted);
}
</style>
