"""Tests for reply extraction — must not leak prior-turn task results."""

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from subagent.stone.runtime.trace import extract_reply


def test_greeting_after_db_query_uses_current_ai_only():
    messages = [
        HumanMessage(content="查 orders 表全部数据"),
        AIMessage(content="", tool_calls=[{"name": "task", "args": {}, "id": "1"}]),
        ToolMessage(
            content="orders 表全部数据（共 3 条）：\n| id | customer_id |\n| 1 | 1 |",
            name="task",
            tool_call_id="1",
        ),
        AIMessage(content="以上是 orders 表查询结果。"),
        HumanMessage(content="你好"),
        AIMessage(content="你好！有什么可以帮你的吗？"),
    ]
    assert extract_reply(messages) == "你好！有什么可以帮你的吗？"


def test_current_turn_still_prefers_task_when_delegated():
    messages = [
        HumanMessage(content="查订单"),
        AIMessage(content="我来帮你查。", tool_calls=[{"name": "task", "args": {}, "id": "2"}]),
        ToolMessage(
            content="订单共 100 条，金额合计 50000 元。",
            name="task",
            tool_call_id="2",
        ),
        AIMessage(content="查询完成，结果如下。"),
    ]
    reply = extract_reply(messages)
    assert "订单共 100 条" in reply


def test_single_turn_greeting():
    messages = [
        HumanMessage(content="你好"),
        AIMessage(content="你好！有什么可以帮你的吗？"),
    ]
    assert extract_reply(messages) == "你好！有什么可以帮你的吗？"
