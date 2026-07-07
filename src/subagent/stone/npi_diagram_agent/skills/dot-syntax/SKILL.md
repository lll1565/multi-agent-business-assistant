# DOT 语法速查（写图前过一遍）

## 1. 顶层结构

```
digraph G {            // 有向图
  rankdir=LR;          // LR=左→右，TB=上→下（默认），BT，RL
  node [shape=box style=rounded];   // 全局节点默认样式
  edge [color="#90A4AE"];            // 全局边默认样式
  
  // 节点
  A [label="开始" shape=ellipse fillcolor="#E8F5E9" style=filled];
  
  // 边
  A -> B [label="调用"];
  B -> C;
  C -> A;
}
```

## 2. 常用 shape

| shape | 用途 |
|-------|------|
| `box` | 默认矩形（流程节点） |
| `ellipse` | 椭圆（开始/结束） |
| `diamond` | 菱形（判断） |
| `parallelogram` | 平行四边形（输入/输出） |
| `hexagon` | 六边形（准备） |
| `cylinder` | 圆柱（数据库） |
| `note` | 便签 |
| `subgraph` | 子图（用作 cluster） |

## 3. 颜色（用浅色填充，眼睛舒服）

- 蓝：`#E3F2FD`
- 绿：`#E8F5E9`
- 橙：`#FFF3E0`
- 紫：`#F3E5F5`
- 灰：`#ECEFF1`
- 红：`#FFEBEE`

## 4. 子图分组

```
subgraph cluster_frontend {
  label="前端";
  style=filled;
  fillcolor="#E3F2FD";
  Web; Mobile; CDN;
}

subgraph cluster_backend {
  label="后端";
  style=filled;
  fillcolor="#FFF3E0";
  API; DB; Cache;
}

Web -> API [label="HTTPS"];
API -> DB;
API -> Cache;
```

`cluster_` 前缀必须有才能被识别为子图群组。

## 5. 渲染前自检清单

- [ ] 节点 `label` 都用了双引号
- [ ] 所有 `{` `}` 配对
- [ ] 用了 `rankdir` 控制方向
- [ ] 颜色没超过 4 种
- [ ] 中文 label 测试渲染