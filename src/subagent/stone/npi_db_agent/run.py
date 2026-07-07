"""Standalone CLI for npi_db_agent.

Usage (after `pip install -e .`):
    python -m subagent.stone.npi_db_agent.run "有哪些表"
"""

import sys

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

from subagent.config.paths import resolve_project_root

load_dotenv(resolve_project_root() / ".env")

from subagent.stone.npi_db_agent import create_npi_db_agent


def main() -> None:
    question = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "有哪些表"
    agent = create_npi_db_agent()
    print(f"\n问题: {question}\n")
    result = agent.invoke({"messages": [HumanMessage(content=question)]})
    msg = result["messages"][-1]
    print(msg.content if hasattr(msg, "content") else msg)


if __name__ == "__main__":
    main()
