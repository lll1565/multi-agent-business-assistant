<template>
  <el-card class="answer-table-shell" shadow="never">
    <template #header>
      <div class="answer-table-head">
        <div class="head-left">
          <span class="head-icon"><el-icon><Grid /></el-icon></span>
          <span class="head-title">{{ title }}</span>
          <el-tag size="small" round effect="light" type="info">
            {{ block.rows.length }} 行
          </el-tag>
        </div>
        <div class="table-toolbar">
          <el-button size="small" text @click="copyCsv">
            <el-icon><DocumentCopy /></el-icon>
            复制 CSV
          </el-button>
          <el-button size="small" text type="primary" @click="exportCsv">
            <el-icon><Download /></el-icon>
            导出
          </el-button>
        </div>
      </div>
    </template>
    <div class="answer-table-wrap">
      <el-table
        :data="block.rows"
        stripe
        border
        size="default"
        max-height="400"
        class="answer-data-table"
        empty-text="无数据"
      >
        <el-table-column
          v-for="col in block.columns"
          :key="col.prop"
          :prop="col.prop"
          :label="col.label"
          :min-width="columnMinWidth(col)"
          show-overflow-tooltip
        />
      </el-table>
    </div>
  </el-card>
</template>

<script setup>
import { computed, toRef } from "vue";
import { DocumentCopy, Download, Grid } from "@element-plus/icons-vue";
import { useTableExport } from "../../composables/useTableExport";
import { columnMinWidth, resolveTableTitle } from "../../utils/tableDisplay";

const props = defineProps({
  block: {
    type: Object,
    required: true,
  },
});

const blockRef = toRef(props, "block");
const { copyCsv, exportCsv } = useTableExport(blockRef);

const title = computed(() => resolveTableTitle(props.block));
</script>

<style scoped>
.answer-table-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.head-left {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.head-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--app-text-primary);
}

.table-toolbar {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}
</style>
