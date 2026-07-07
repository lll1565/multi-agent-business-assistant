/** 根据表头推断表格标题（避免「说明」列误判为「能力一览」） */
export function resolveTableTitle(block) {
  const preset = block?.title;
  if (preset && preset !== "查询结果" && preset !== "数据") return preset;

  const labels = (block?.columns || []).map((c) => c.label || "").join("|");
  if (/表名/.test(labels) && (/说明|用途|描述|description/i.test(labels) || (block.columns || []).length <= 3)) {
    return "数据表一览";
  }
  if (/任务|能力|类型/.test(labels) && !/表名/.test(labels)) {
    return "能力一览";
  }
  return preset || "查询结果";
}

export function columnMinWidth(col) {
  const label = col?.label || "";
  const prop = col?.prop || "";
  if (/表名|^name$/i.test(label) || /^name$/i.test(prop)) return 180;
  if (/说明|用途|描述|description/i.test(label)) return 240;
  return Math.max(col?.minWidth || 0, 120);
}
