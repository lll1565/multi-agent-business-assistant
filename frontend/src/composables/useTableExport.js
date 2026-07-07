import { computed } from "vue";
import { ElMessage } from "element-plus";
import {
  buildTableExportFilename,
  copyTextToClipboard,
  downloadTextFile,
  tableBlockToCsv,
} from "../modules/table-export";

/**
 * @param {import('vue').MaybeRefOrGetter<{ columns: { prop: string, label: string }[], rows: Record<string, unknown>[], title?: string }>} blockSource
 */
export function useTableExport(blockSource) {
  const csvText = computed(() => tableBlockToCsv(resolveBlock(blockSource)));

  async function copyCsv() {
    const text = csvText.value;
    if (!text) {
      ElMessage.warning("暂无数据可复制");
      return;
    }
    try {
      await copyTextToClipboard(text);
      ElMessage.success("已复制 CSV 到剪贴板");
    } catch {
      ElMessage.error("复制失败，请检查浏览器权限");
    }
  }

  function exportCsv() {
    const text = csvText.value;
    if (!text) {
      ElMessage.warning("暂无数据可导出");
      return;
    }
    const block = resolveBlock(blockSource);
    downloadTextFile(buildTableExportFilename(block), text);
    ElMessage.success("已开始下载");
  }

  return { csvText, copyCsv, exportCsv };
}

function resolveBlock(source) {
  if (typeof source === "function") return source();
  if (source && typeof source === "object" && "value" in source) return source.value;
  return source;
}
