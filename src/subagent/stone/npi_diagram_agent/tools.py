"""Diagram rendering tools for npi_diagram_agent."""

from __future__ import annotations

import os
import re
import shutil
import time
from langchain_core.tools import tool
from pathlib import Path
from subagent.config.logging_setup import get_logger
from subagent.config.paths import resolve_project_root

logger = get_logger("agent.diagram_tools")

_PROJECT_ROOT = resolve_project_root()
_DIAGRAM_DIR = _PROJECT_ROOT / "data" / "diagrams"
_VALID_FORMATS = ("png", "svg", "pdf", "dot")
_VALID_ENGINES = ("dot", "neato", "fdp", "sfdp", "circo", "twopi", "patchwork", "osage")

_SAFE_NAME = re.compile(r"[^A-Za-z0-9_.-]+")

_WIN_DOT_CANDIDATES = (
    r"C:\Program Files\Graphviz\bin\dot.exe",
    r"C:\Program Files (x86)\Graphviz\bin\dot.exe",
    r"D:\software\Graphviz\bin\dot.exe",
    r"D:\Program Files\Graphviz\bin\dot.exe",
)


def _resolve_dot_binary() -> str | None:
    env_bin = os.environ.get("GRAPHVIZ_BIN")
    if env_bin and Path(env_bin).is_file():
        return str(Path(env_bin).resolve())

    env_dir = os.environ.get("GRAPHVIZ_BIN_DIR")
    if env_dir:
        cand = Path(env_dir) / ("dot.exe" if os.name == "nt" else "dot")
        if cand.is_file():
            return str(cand.resolve())

    for cand in _WIN_DOT_CANDIDATES:
        if Path(cand).is_file():
            return str(Path(cand).resolve())

    which = shutil.which("dot")
    if which:
        return str(Path(which).resolve())
    return None


def _safe_filename(name: str) -> str:
    name = (name or "diagram").strip().strip(".")
    name = _SAFE_NAME.sub("_", name) or "diagram"
    return name[:64]


def _ensure_diagram_dir() -> Path:
    _DIAGRAM_DIR.mkdir(parents=True, exist_ok=True)
    return _DIAGRAM_DIR


def _format_size(num_bytes: int) -> str:
    if num_bytes < 1024:
        return f"{num_bytes} B"
    if num_bytes < 1024 * 1024:
        return f"{num_bytes / 1024:.1f} KB"
    return f"{num_bytes / 1024 / 1024:.2f} MB"


def _check_dot_available() -> tuple[bool, str]:
    try:
        import graphviz  # type: ignore
    except ImportError:
        return False, "python-graphviz 包未安装"
    bin_path = _resolve_dot_binary()
    if not bin_path:
        return False, "未找到 dot 二进制（请设 GRAPHVIZ_BIN 或装 graphviz）"
    try:
        probe_dir = _PROJECT_ROOT / "data" / ".gvprobe"
        probe_dir.mkdir(parents=True, exist_ok=True)
        try:
            src = graphviz.Source("digraph G { a }", format="png", engine="dot")
            src.render(filename="__gv_probe", directory=str(probe_dir), cleanup=True)
        finally:
            shutil.rmtree(probe_dir, ignore_errors=True)
    except graphviz.ExecutableNotFound as exc:  # type: ignore[attr-defined]
        return False, f"graphviz 执行失败: {exc}"
    except Exception as exc:  # noqa: BLE001
        return False, f"graphviz 错误: {type(exc).__name__}: {exc}"
    return True, "ok"


@tool
def render_diagram(
    dot_code: str,
    output_name: str = "diagram",
    output_format: str = "png",
    engine: str = "dot",
) -> str:
    """Render a Graphviz DOT diagram to PNG/SVG/PDF."""
    if not dot_code or not dot_code.strip():
        return "【render_diagram】DOT 代码不能为空"
    output_format = (output_format or "png").lower().strip()
    if output_format not in _VALID_FORMATS:
        return f"【render_diagram】不支持的格式 {output_format}（可选 {', '.join(_VALID_FORMATS)}）"
    engine = (engine or "dot").lower().strip()
    if engine not in _VALID_ENGINES:
        return f"【render_diagram】不支持的 engine: {engine}（可选 {', '.join(_VALID_ENGINES)}）"

    safe_name = _safe_filename(output_name)
    timestamp = int(time.time() * 1000)
    filename = f"{safe_name}_{timestamp}"

    if output_format == "dot":
        return f"```dot\n{dot_code.strip()}\n```"

    ok, msg = _check_dot_available()
    if not ok:
        logger.warning("render_diagram: graphviz unavailable (%s)", msg)
        return (
            f"【render_diagram】{msg}。已返回 DOT 源码，可用以下方式渲染：\n"
            "  — 安装：https://graphviz.org/download/ 或 `winget install graphviz`\n"
            "  — 在线：https://dreampuf.github.io/GraphvizOnline/\n"
            "  — 自定义：设环境变量 GRAPHVIZ_BIN=D:\\path\\to\\dot.exe\n\n"
            f"```dot\n{dot_code.strip()}\n```"
        )

    out_dir = _ensure_diagram_dir()

    try:
        import graphviz  # type: ignore

        bin_path = _resolve_dot_binary()
        old_path = os.environ.get("PATH", "")
        if bin_path:
            bin_dir = str(Path(bin_path).parent)
            if bin_dir not in old_path:
                os.environ["PATH"] = bin_dir + os.pathsep + old_path

        src = graphviz.Source(
            dot_code,
            format=output_format,
            engine=engine if engine != "dot" else "dot",
        )
        rendered = src.render(filename=filename, directory=str(out_dir), cleanup=True)
        rendered_path = Path(rendered)
        if not rendered_path.is_absolute():
            rendered_path = out_dir / rendered_path
        rel = rendered_path.relative_to(_PROJECT_ROOT).as_posix()
        size = rendered_path.stat().st_size if rendered_path.exists() else 0
        return f"![{safe_name}]({rel})\n\n已渲染到 `{rel}` ({_format_size(size)}, engine={engine})"
    except Exception as exc:  # noqa: BLE001
        logger.warning("render_diagram failed: %s: %s", type(exc).__name__, exc)
        return (
            f"【render_diagram】渲染失败：{type(exc).__name__}: {exc}。已返回 DOT 源码。\n\n"
            f"```dot\n{dot_code.strip()}\n```"
        )


def get_diagram_tools() -> list:
    return [render_diagram]
