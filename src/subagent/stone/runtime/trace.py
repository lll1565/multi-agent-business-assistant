"""Extract reasoning trace from LangGraph / Deep Agent messages."""

import json
import re
from typing import Any

AGENT_LABELS = {
    "npi_db_agent": "数据库 Agent (npi_db_agent)",
    "npi_api_agent": "API 文档 Agent (npi_api_agent)",
    "general-purpose": "通用子 Agent",
}

TOOL_LABELS = {
    "task": "委派子 Agent",
    "write_todos": "任务规划 (write_todos)",
    "sql_db_list_tables": "列出数据库表",
    "sql_db_schema": "查看表结构",
    "sql_db_query": "执行 SQL 查询",
    "query_checker": "校验 SQL",
    "read_file": "读取文件/技能",
    "write_file": "写入文件",
    "ls": "列出目录",
    "glob": "搜索文件",
    "grep": "搜索内容",
    "query_api_doc": "查询 API 文档",
    "list_all_apis": "列出全部 API",
}


def _msg_type(msg: Any) -> str:
    return getattr(msg, "type", "") or msg.__class__.__name__.lower().replace("message", "")


def _msg_content(msg: Any) -> str:
    c = getattr(msg, "content", "")
    if isinstance(c, list):
        parts = []
        for block in c:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
            elif isinstance(block, str):
                parts.append(block)
        return "\n".join(parts)
    return str(c) if c else ""


def _extract_thinking(text: str) -> str | None:
    m = re.search(
        r"<think>(.*?)</think>",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )
    return m.group(1).strip() if m else None


def _clean_reply(text: str) -> str:
    text = re.sub(
        r"<think>.*?</think>",
        "",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )
    return text.strip()


def _tool_calls(msg: Any) -> list[dict]:
    calls = getattr(msg, "tool_calls", None) or []
    out = []
    for tc in calls:
        if isinstance(tc, dict):
            out.append(tc)
        else:
            out.append(
                {
                    "name": getattr(tc, "name", ""),
                    "args": getattr(tc, "args", {}) or {},
                    "id": getattr(tc, "id", ""),
                }
            )
    return out


def _summarize_tool_result(name: str, content: str, max_len: int = 200) -> str:
    text = content.strip()
    if len(text) > max_len:
        text = text[:max_len] + "…"
    if name == "sql_db_query":
        return text
    if name == "task":
        return text[:300] + ("…" if len(content) > 300 else "")
    return text


def _messages_this_turn(messages: list[Any]) -> list[Any]:
    last_human = -1
    for i, msg in enumerate(messages):
        if _msg_type(msg) == "human":
            last_human = i
    return messages[last_human + 1 :] if last_human >= 0 else messages


def merge_nested_traces(
    supervisor_trace: dict[str, Any], nested_traces: list[dict[str, Any]]
) -> dict[str, Any]:
    """Insert sub-agent tool/SQL steps right after each delegate step."""
    if not nested_traces:
        return supervisor_trace

    merged_steps: list[dict[str, str]] = []
    agents_used = list(supervisor_trace.get("agents_used") or [])
    sub_idx = 0

    for step in supervisor_trace.get("steps") or []:
        merged_steps.append(step)
        if step.get("type") != "delegate":
            continue
        if sub_idx >= len(nested_traces):
            break
        nested = nested_traces[sub_idx]
        sub_idx += 1
        agent_key = nested.get("agent", "")
        agent_label = AGENT_LABELS.get(agent_key, agent_key)
        for sub_step in nested.get("steps") or []:
            title = sub_step.get("title", "")
            merged_steps.append(
                {
                    "type": f"sub_{sub_step.get('type', 'tool')}",
                    "title": f"[{agent_label}] {title}",
                    "detail": sub_step.get("detail"),
                    "agent": agent_key,
                }
            )

    while sub_idx < len(nested_traces):
        nested = nested_traces[sub_idx]
        sub_idx += 1
        agent_key = nested.get("agent", "")
        agent_label = AGENT_LABELS.get(agent_key, agent_key)
        for sub_step in nested.get("steps") or []:
            merged_steps.append(
                {
                    "type": f"sub_{sub_step.get('type', 'tool')}",
                    "title": f"[{agent_label}] {sub_step.get('title', '')}",
                    "detail": sub_step.get("detail"),
                    "agent": agent_key,
                }
            )

    for nested in nested_traces:
        agent_key = nested.get("agent", "")
        if agent_key and agent_key not in agents_used:
            agents_used.append(agent_key)

    return {
        "agents_used": agents_used,
        "agent_labels": [AGENT_LABELS.get(a, a) for a in agents_used],
        "steps": merged_steps,
    }


def build_trace(messages: list[Any]) -> dict[str, Any]:
    """Build reasoning steps and agents_used from agent message list."""
    steps: list[dict[str, str]] = []
    agents_used: list[str] = []

    for msg in _messages_this_turn(messages):
        mtype = _msg_type(msg)

        if mtype == "ai":
            content = _msg_content(msg)
            thinking = _extract_thinking(content)
            if thinking:
                steps.append(
                    {
                        "type": "thinking",
                        "title": "推理思考",
                        "detail": thinking,
                    }
                )

            for tc in _tool_calls(msg):
                name = tc.get("name", "")
                args = tc.get("args") or {}
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError:
                        args = {"raw": args}

                label = TOOL_LABELS.get(name, name)

                if name == "task":
                    agent_key = args.get("subagent_type") or args.get("name") or "unknown"
                    if agent_key not in agents_used:
                        agents_used.append(agent_key)
                    agent_label = AGENT_LABELS.get(agent_key, agent_key)
                    desc = args.get("description", "")
                    steps.append(
                        {
                            "type": "delegate",
                            "title": f"委派 → {agent_label}",
                            "detail": desc or None,
                            "agent": agent_key,
                        }
                    )
                elif name == "write_todos":
                    todos = args.get("todos") or args
                    detail = json.dumps(todos, ensure_ascii=False, indent=2)
                    if len(detail) > 500:
                        detail = detail[:500] + "…"
                    steps.append(
                        {
                            "type": "plan",
                            "title": label,
                            "detail": detail,
                        }
                    )
                else:
                    detail_parts = []
                    for k, v in args.items() if isinstance(args, dict) else []:
                        detail_parts.append(f"{k}: {v}")
                    steps.append(
                        {
                            "type": "tool",
                            "title": label,
                            "detail": "\n".join(detail_parts) or None,
                        }
                    )

        elif mtype == "tool":
            name = getattr(msg, "name", "") or ""
            content = _msg_content(msg)
            if name == "task":
                if content and len(content.strip()) > 20:
                    steps.append(
                        {
                            "type": "sub_summary",
                            "title": "子 Agent 返回摘要",
                            "detail": _summarize_tool_result(name, content, max_len=400),
                        }
                    )
                continue
            if content:
                steps.append(
                    {
                        "type": "tool_result",
                        "title": f"{TOOL_LABELS.get(name, name)} 结果",
                        "detail": _summarize_tool_result(name, content),
                    }
                )

    return {
        "agents_used": agents_used,
        "agent_labels": [AGENT_LABELS.get(a, a) for a in agents_used],
        "steps": steps,
    }


def build_thinking_narrative(trace: dict[str, Any]) -> str:
    """Plain-text narrative for frontend thinking stream (hard route / snapshot paths)."""
    parts: list[str] = []
    for step in trace.get("steps") or []:
        t = step.get("type") or ""
        if t in ("thinking", "sub_thinking"):
            d = (step.get("detail") or "").strip()
            if d:
                parts.append(d)
        elif t == "delegate":
            d = (step.get("detail") or step.get("title") or "").strip()
            if d:
                parts.append(d)
        elif t in ("tool", "sub_tool"):
            title = (step.get("title") or "").strip()
            if title:
                parts.append(title)
        elif t == "plan":
            d = (step.get("detail") or "").strip()
            if d:
                parts.append(d)
        elif t == "info":
            d = (step.get("detail") or "").strip()
            if d:
                parts.append(d)
    return "\n\n".join(parts)


_WEAK_REPLY_MARKERS = (
    "以上",
    "完整文档",
    "已经通过",
    "已经获取",
    "已经查询",
    "汇总如下",
    "如下所",
    "再次请求",
    "委派",
)


def _has_substantive_body(text: str) -> bool:
    """True when reply looks like real data/docs, not a one-line wrap-up."""
    t = text.strip()
    if len(t) >= 120:
        return True
    markers = ("【API文档】", "/api/", "| ", "```", "GET ", "POST ", "PUT ", "DELETE ")
    return any(m in t for m in markers)


def _is_meta_only_reply(text: str) -> bool:
    t = text.strip()
    if not t:
        return True
    if _has_substantive_body(t):
        return False
    if len(t) < 80:
        return True
    return any(m in t for m in _WEAK_REPLY_MARKERS)


def extract_reply(messages: list[Any]) -> str:
    """Pick the best user-facing answer from the **current turn** only."""
    turn_messages = _messages_this_turn(messages)
    last_ai = ""
    last_task = ""

    for msg in reversed(turn_messages):
        mtype = _msg_type(msg)
        if mtype == "ai" and not last_ai:
            content = _clean_reply(_msg_content(msg))
            if content:
                last_ai = content
        elif mtype == "tool" and not last_task:
            name = getattr(msg, "name", "") or ""
            if name == "task":
                content = _clean_reply(_msg_content(msg))
                if content and len(content.strip()) > 20:
                    last_task = content
        if last_ai and last_task:
            break

    if not last_task:
        return last_ai

    if _is_meta_only_reply(last_ai) or len(last_task) > len(last_ai) + 40:
        return last_task
    return last_ai or last_task


def message_chunk_text(chunk: Any) -> str:
    """Extract text delta from a streamed message chunk."""
    if chunk is None:
        return ""
    content = getattr(chunk, "content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
            elif isinstance(block, str):
                parts.append(block)
        return "".join(parts)
    return str(content) if content else ""
