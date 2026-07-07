"""Fast path for greetings / capability / help - no LLM, no sub-agent delegation."""

from __future__ import annotations

import re
from subagent.stone.routing.capability_catalog import build_capability_reply, build_greeting_reply

_META_PATTERNS = re.compile(
    r"^(?:"
    r"你(?:能|可以)(?:做|干)什么|"
    r"你(?:会|能)什么|"
    r"有什么(?:功能|能力)|"
    r"能帮我什么|"
    r"怎么用|如何使用|使用说明|"
    r"帮助|help|"
    r"你是谁|你是什么|介绍一下?你|"
    r"你是干什么的|"
    r"你好|您好|hello|hi"
    r")\s*[？?！!。.]*$",
    re.IGNORECASE,
)


def is_meta_query(message: str) -> bool:
    text = (message or "").strip()
    if not text or len(text) > 80:
        return False
    return bool(_META_PATTERNS.match(text))


def _is_greeting_only(text: str) -> bool:
    return bool(re.match(r"^(?:你好|您好|hello|hi)\s*[。！？?!]*$", text, re.IGNORECASE))


def build_meta_reply(message: str) -> str:
    text = (message or "").strip()
    if _is_greeting_only(text):
        return build_greeting_reply()
    return build_capability_reply()


def _build_meta_trace() -> dict:
    return {
        "agents_used": [],
        "agent_labels": [],
        "steps": [
            {
                "type": "info",
                "title": "元问题快路径",
                "detail": "问候/能力咨询，从注册中心生成能力说明，不委派 Agent。",
            }
        ],
    }


def try_meta_fast_path(user_message: str) -> dict | None:
    if not is_meta_query(user_message):
        return None
    return {
        "reply": build_meta_reply(user_message),
        "trace": _build_meta_trace(),
    }
