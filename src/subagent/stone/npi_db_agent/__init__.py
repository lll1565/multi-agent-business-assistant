"""NPI database subagent (Deep Agent + skills)."""

import re

from subagent.stone.routing.registry import SubAgentSpec
from subagent.stone.routing.routing_intents import DB_TABLE_NAMES
from subagent.stone.safety import SafetyRule

from .sub_agent import create_npi_db_agent

_DB_KEYWORDS = (
    "数据库",
    "数据表",
    "表结构",
    "sql",
    "select",
    "查询",
    "订单",
    "客户",
    "产品",
    "库存",
    "供应商",
    "分类",
    "支付",
    "明细",
    "sku",
    *DB_TABLE_NAMES,
    "demo.db",
    "有哪些表",
    "列出表",
    re.compile(r"查.*表"),
    re.compile(r"表.*数据"),
)

AGENT_SPEC = SubAgentSpec(
    name="npi_db_agent",
    description=(
        "查询 SQLite 业务库 demo.db（categories/suppliers/products/"
        "customers/orders/order_items/payments/inventory 等），"
        "只读 SQL，默认 LIMIT 5。使用 skills 目录下的 SQL 技能。"
        "会话 checkpoint 存 chat.db，独立于 demo 业务库。"
    ),
    factory=create_npi_db_agent,
    keywords=_DB_KEYWORDS,
    kind="db",
    supports_hard_route=True,
    uses_persistent_checkpointer=True,
    capability_title="数据库查询",
    capability_bullets=(
        "查看有哪些表、表结构说明",
        "查询订单、客户、商品、库存、支付等业务数据",
        "做简单统计与汇总（只读，不会修改数据）",
    ),
    capability_examples=(
        "数据库里有哪些表？",
        "列出前 5 条订单记录",
    ),
    capability_order=10,
    safety_rules=(
        SafetyRule.READ_ONLY_SQL,
        SafetyRule.DEFAULT_ROW_LIMIT_5,
    ),
)

__all__ = ["create_npi_db_agent", "AGENT_SPEC"]
