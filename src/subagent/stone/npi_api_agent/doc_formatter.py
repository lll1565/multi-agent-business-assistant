"""将 API 元数据格式化为前端可渲染 Markdown（表格 + JSON 代码块）。"""

from __future__ import annotations

import json
from typing import Any


def _pretty_json(raw: str) -> str:
    try:
        parsed = json.loads(raw)
        return json.dumps(parsed, ensure_ascii=False, indent=2)
    except (json.JSONDecodeError, TypeError):
        return raw


def _params_table(params: dict[str, str]) -> str:
    if not params:
        return "_无请求参数_\n"
    lines = [
        "| 参数名 | 类型与说明 |",
        "|--------|------------|",
    ]
    for key, desc in params.items():
        lines.append(f"| `{key}` | {desc} |")
    return "\n".join(lines) + "\n"


def format_single_api(name: str, doc: dict[str, Any]) -> str:
    """单个接口文档（Swagger 风格 Markdown）。"""
    method = doc.get("method", "")
    path = doc.get("path", "")
    desc = doc.get("description", "")
    response = _pretty_json(str(doc.get("response", "")))

    return f"""## {name}

> {desc}

| 项目 | 内容 |
|------|------|
| 方法 | **{method}** |
| 路径 | `{path}` |

### 请求参数

{_params_table(doc.get("params") or {})}
### 响应示例

```json
{response}
```
"""


def format_api_doc_results(matches: list[tuple[str, dict[str, Any]]]) -> str:
    if not matches:
        return ""
    parts = ["## API 接口文档\n"]
    for name, doc in matches:
        parts.append(format_single_api(name, doc).strip())
    return "\n\n".join(parts)


def format_all_apis_list(docs: dict[str, dict[str, Any]]) -> str:
    lines = [
        "## API 接口列表",
        "",
        "| 方法 | 路径 | 说明 |",
        "|------|------|------|",
    ]
    for name, doc in docs.items():
        method = doc.get("method", "")
        path = doc.get("path", "")
        desc = doc.get("description", "")
        lines.append(f"| **{method}** | `{path}` | {desc} |")
    lines.append("")
    lines.append("_提示：可继续提问某个接口名，例如「查 get_users 接口文档」_")
    return "\n".join(lines)


def format_not_found(all_docs: dict[str, dict[str, Any]], query: str) -> str:
    return f"## API 接口文档\n\n未找到与 **{query}** 匹配的接口。\n\n" + format_all_apis_list(
        all_docs
    )
