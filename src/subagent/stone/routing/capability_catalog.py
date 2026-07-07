"""Build user-facing capability text from registered sub-agents."""

from __future__ import annotations

from subagent.stone.routing.registry import SubAgentSpec, discover_stone_agents, get_registry

_DEFAULT_KIND_TITLES: dict[str, str] = {
    "db": "数据库查询",
    "api": "API 接口文档",
    "web": "网页搜索",
    "diagram": "图表绘制",
}


def resolve_capability_title(spec: SubAgentSpec) -> str:
    title = (spec.capability_title or "").strip()
    if title:
        return title
    return _DEFAULT_KIND_TITLES.get(spec.kind, spec.kind or "其他能力")


def sorted_capability_specs() -> tuple[SubAgentSpec, ...]:
    discover_stone_agents()
    return tuple(
        sorted(
            get_registry().all(),
            key=lambda spec: (spec.capability_order, spec.name),
        )
    )


def _capability_bullets(spec: SubAgentSpec) -> tuple[str, ...]:
    if spec.capability_bullets:
        return spec.capability_bullets
    desc = (spec.description or "").strip()
    if not desc:
        return ()
    first = desc.split("。")[0].split(".")[0].strip()
    if first:
        return (first + "。",)
    return (desc,)


def build_capability_section(spec: SubAgentSpec) -> str:
    lines = [f"### {resolve_capability_title(spec)}"]
    for bullet in _capability_bullets(spec):
        lines.append(f"- {bullet}")
    if spec.capability_examples:
        lines.append("")
        lines.append("**可以试试：**")
        for example in spec.capability_examples:
            lines.append(f"- 「{example}」")
    return "\n".join(lines)


def build_capability_reply() -> str:
    specs = sorted_capability_specs()
    if not specs:
        return (
            "## 我能帮你做什么\n\n"
            "我是 **Stone 多智能体助手**。当前暂无已注册的能力模块。"
        )

    sections = "\n\n".join(build_capability_section(spec) for spec in specs)
    count = len(specs)
    return (
        "## 我能帮你做什么\n\n"
        f"我是 **Stone 多智能体助手**，用自然语言理解你的需求，"
        f"并自动完成下面 {count} 类任务：\n\n"
        f"{sections}\n\n"
        "---\n\n"
        "直接说出你的问题即可，我会自动选择合适的工具。"
    )


def build_greeting_reply() -> str:
    specs = sorted_capability_specs()
    if not specs:
        return (
            "你好！我是 **Stone 多智能体助手**。\n"
            "有什么需要，直接说就好——**不用记命令**。"
        )

    titles = [resolve_capability_title(spec) for spec in specs]
    if len(titles) == 1:
        caps = f"**{titles[0]}**"
    elif len(titles) == 2:
        caps = f"**{titles[0]}** 和 **{titles[1]}**"
    else:
        caps = "、".join(f"**{title}**" for title in titles[:-1]) + f"和 **{titles[-1]}**"

    return (
        f"你好！我是 **Stone 多智能体助手**。\n"
        f"我可以帮你：{caps}。\n"
        "有什么需要，直接说就好——**不用记命令**。"
    )
