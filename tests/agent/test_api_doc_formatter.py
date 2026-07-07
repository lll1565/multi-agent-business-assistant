from subagent.stone.npi_api_agent.doc_formatter import format_single_api


def test_format_single_api_has_tables_and_json_fence():
    doc = {
        "method": "GET",
        "path": "/api/users",
        "description": "获取用户列表",
        "params": {"page": "int，页码"},
        "response": '{"code": 0}',
    }
    text = format_single_api("get_users", doc)
    assert "## get_users" in text
    assert "### 请求参数" in text
    assert "| 参数名 |" in text
    assert "```json" in text


def test_format_includes_meta_table():
    text = format_single_api(
        "get_users",
        {
            "method": "GET",
            "path": "/api/users",
            "description": "获取用户列表",
            "params": {},
            "response": "{}",
        },
    )
    assert "| 项目 |" in text
    assert "**GET**" in text
