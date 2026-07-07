"""NPI diagram subagent (Graphviz DOT -> PNG/SVG, graceful fallback)."""

import re
from subagent.stone.routing.registry import SubAgentSpec, cancel_when_not_diagram
from subagent.stone.routing.routing_intents import DIAGRAM_EXCLUSIVE_KEYWORDS

from .sub_agent import create_npi_diagram_agent

_DIAGRAM_KEYWORDS = (
    "画",
    "绘制",
    "流程图",
    "架构图",
    "时序图",
    "状态图",
    "类图",
    "用例图",
    "拓扑图",
    "思维导图",
    "依赖图",
    "关系图",
    "结构图",
    "示意图",
    "组织图",
    "网络图",
    "组件图",
    "部署图",
    "ER图",
    "E-R图",
    "uml",
    "图形",
    "图表",
    "可视化",
    "生成图",
    "做图",
    "画图",
    "出图",
    "渲染图",
    "diagram",
    "flowchart",
    "flow chart",
    "architecture diagram",
    "sequence diagram",
    "state diagram",
    "class diagram",
    "use case",
    "topology",
    "mindmap",
    "mind map",
    "dependency graph",
    "ER diagram",
    "block diagram",
    "render",
    "plot",
    "graph",
    "DOT",
    "graphviz",
    "draw",
    "digraph",
    re.compile(r"画\s*(?:一|个|张|幅)?"),
    re.compile(r"帮我\s*(?:画|绘|做|生成)?"),
)

AGENT_SPEC = SubAgentSpec(
    name="npi_diagram_agent",
    description=(
        "将 **Graphviz DOT** 源码渲染为 PNG/SVG/PDF；"
        "无 dot 二进制时返回 DOT 源码块。"
        "适合流程图、架构图、ER 图等。"
        "**不负责**照片/艺术画/Logo。"
    ),
    factory=create_npi_diagram_agent,
    keywords=_DIAGRAM_KEYWORDS,
    exclusive_keywords=DIAGRAM_EXCLUSIVE_KEYWORDS,
    exclusive_cancel_keywords=cancel_when_not_diagram(),
    kind="diagram",
    capability_title="图表绘制",
    capability_bullets=(
        "绘制流程图、架构图、时序图、ER 图等",
        "输出 Graphviz 渲染图或 DOT 源码",
    ),
    capability_examples=(
        "画一个下单流程图",
        "生成订单系统的架构图",
    ),
    capability_order=40,
)

__all__ = ["create_npi_diagram_agent", "AGENT_SPEC"]
