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
            "我是一个多能力助手。当前暂无已注册的能力。"
        )

    sections = "\n\n".join(build_capability_section(spec) for spec in specs)
    count = len(specs)
    flow = " → ".join(resolve_capability_title(spec) for spec in specs)
    return (
        "## 我能帮你做什么\n\n"
        f"我是一个面向业务查询与知识检索的多能力助手。你直接描述需求即可，"
        f"我会在下面 {count} 类能力中选择合适路径：\n\n"
        f"{sections}\n\n"
        "### 系统工作流程\n"
        "- 理解你的问题\n"
        "- 选择匹配的能力路径\n"
        "- 获取或生成结果\n"
        "- 整理成可阅读的中文回答\n\n"
        f"当前能力覆盖：{flow}。\n\n"
        "---\n\n"
        "直接说出你的问题即可。"
    )


def build_greeting_reply() -> str:
    specs = sorted_capability_specs()
    if not specs:
        return (
            "你好！我是一个多能力助手。\n"
            "有什么需要，直接说就好，不用记命令。"
        )

    titles = [resolve_capability_title(spec) for spec in specs]
    if len(titles) == 1:
        caps = f"**{titles[0]}**"
    elif len(titles) == 2:
        caps = f"**{titles[0]}** 和 **{titles[1]}**"
    else:
        caps = "、".join(f"**{title}**" for title in titles[:-1]) + f"和 **{titles[-1]}**"

    return (
        f"你好！我是一个多能力助手。\n"
        f"我可以帮你：{caps}。\n"
        "有什么需要，直接说就好，不用记命令。"
    )
