"""CLI demo - invoke stone supervisor without FastAPI."""

from subagent.stone.runtime.core import chat


def main() -> None:
    print("\n" + "=" * 70)
    print("MULTI-AGENT CLI DEMO: src/subagent/stone")
    print("=" * 70)
    print(
        "\nSamples:\n"
        "  - '数据库里有哪些表？'         -> npi_db_agent\n"
        "  - '查 get_users 接口文档'    -> npi_api_agent\n"
        "  - '联网搜索 Python 教程'     -> npi_web_agent\n"
    )

    samples = [
        ("数据库里有哪些表？", "npi_db_agent"),
        ("查 get_users 接口文档", "npi_api_agent"),
    ]

    for user_msg, expected in samples:
        print("-" * 50)
        print(f"USER: {user_msg}")
        print(f"  expected route: {expected}")
        try:
            response = chat(user_msg)
            print(f"ASSISTANT: {response}\n")
        except Exception as exc:
            print(f"ERROR: [{type(exc).__name__}] {exc}\n")


if __name__ == "__main__":
    main()
