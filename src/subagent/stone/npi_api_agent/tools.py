"""API documentation tools for npi_api_agent."""

from langchain_core.tools import tool

from subagent.config.logging_setup import get_logger
from subagent.stone.npi_api_agent.doc_formatter import (
    format_all_apis_list,
    format_api_doc_results,
    format_not_found,
)

logger = get_logger("agent.api_tools")

_API_DOCS = {
    "get_users": {
        "method": "GET",
        "path": "/api/users",
        "description": "获取用户列表",
        "params": {"page": "int，页码", "limit": "int，每页数量"},
        "response": '{"code": 0, "data": [{"id": 1, "name": "张三"}]}',
    },
    "get_user": {
        "method": "GET",
        "path": "/api/users/{id}",
        "description": "获取单个用户",
        "params": {"id": "int，用户 ID"},
        "response": '{"code": 0, "data": {"id": 1, "name": "张三"}}',
    },
    "create_user": {
        "method": "POST",
        "path": "/api/users",
        "description": "创建用户",
        "params": {"name": "str，用户名", "email": "str，邮箱"},
        "response": '{"code": 0, "message": "创建成功"}',
    },
    "update_user": {
        "method": "PUT",
        "path": "/api/users/{id}",
        "description": "更新用户",
        "params": {"id": "int", "name": "str，用户名", "email": "str，邮箱"},
        "response": '{"code": 0, "message": "更新成功"}',
    },
    "delete_user": {
        "method": "DELETE",
        "path": "/api/users/{id}",
        "description": "删除用户",
        "params": {"id": "int，用户 ID"},
        "response": '{"code": 0, "message": "删除成功"}',
    },
    "login": {
        "method": "POST",
        "path": "/api/login",
        "description": "用户登录",
        "params": {"username": "str，用户名", "password": "str，密码"},
        "response": '{"code": 0, "token": "xxx"}',
    },
}


@tool
def query_api_doc(api_name: str) -> str:
    """Query API documentation by name or keyword."""
    logger.info("query_api_doc api_name=%r", api_name)
    api_name_lower = api_name.lower()
    matches = []
    for name, doc in _API_DOCS.items():
        if (
            api_name_lower in name.lower()
            or api_name_lower in doc["path"].lower()
            or api_name_lower in doc["description"].lower()
        ):
            matches.append((name, doc))

    if not matches:
        return format_not_found(_API_DOCS, api_name)

    return format_api_doc_results(matches)


@tool
def list_all_apis() -> str:
    """List all available APIs."""
    logger.info("list_all_apis")
    return format_all_apis_list(_API_DOCS)


def get_api_tools() -> list:
    return [query_api_doc, list_all_apis]
