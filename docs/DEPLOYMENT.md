# 部署说明

本文说明如何在 Windows 本地和 Docker Compose 环境运行本项目。项目定位为学习和展示用途，不宣称为完整生产系统。

## 1. 版本要求

- Python 3.11
- Node.js 22
- npm
- Docker Desktop（Docker 部署时需要）
- Graphviz 可选

Graphviz 说明：

- 本地未安装 Graphviz 时，图表能力会降级返回 DOT 源码。
- Docker 后端镜像安装 Graphviz，容器内 `dot` 命令可用。

## 2. Windows 本地部署

以下命令均从项目根目录执行。

### 2.1 创建 Python 虚拟环境

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2.2 安装后端依赖

```powershell
pip install -e ".[dev]"
```

### 2.3 准备环境变量

```powershell
copy .env.example .env
```

编辑 `.env`，填写模型接口配置：

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://example-openai-compatible-endpoint/v1
OPENAI_MODEL=your-model-name
```

不要把真实 `.env` 提交到仓库。

### 2.4 初始化演示业务库

```powershell
multi-agent-init-demo
```

如果命令不可用，也可以使用：

```powershell
python scripts/demo_db.py
```

### 2.5 安装前端依赖

```powershell
cd frontend
npm ci
cd ..
```

### 2.6 启动后端

```powershell
.\scripts\run_backend.ps1
```

后端地址：

- `http://127.0.0.1:8010`
- Swagger：`http://127.0.0.1:8010/api/docs`

### 2.7 启动前端

另开一个终端，从项目根目录执行：

```powershell
.\scripts\run_frontend.ps1
```

前端地址：

- `http://127.0.0.1:5143`

## 3. Docker Compose 部署

Docker 使用两个服务：

- `backend`：FastAPI + Agent + SQLite + Graphviz，端口 `8010`
- `frontend`：Nginx 托管 Vue 构建产物，端口 `5143`

### 3.1 准备配置

```bash
cp .env.example .env
```

填写 `.env` 中的模型接口配置。`.env` 只在 compose 运行时注入，不会复制进镜像。

### 3.2 启动

```bash
docker compose up --build
```

访问：

- 前端页面：`http://localhost:5143`
- Swagger：`http://localhost:8010/api/docs`
- 健康检查：`http://localhost:8010/api/health`

### 3.3 数据持久化

Compose 将本机 `./data` 挂载到后端容器 `/app/data`：

- `/app/data/demo.db`
- `/app/data/chat.db`
- `/app/data/agent_checkpoints.db`
- `/app/data/logs/`

后端入口脚本会在 `demo.db` 不存在时自动初始化演示业务库。

## 4. 端口

| 服务 | 端口 |
|---|---|
| backend | `8010` |
| frontend | `5143` |

端口配置来源于 `src/backend/config/ports.json`，本地脚本和 Vite 配置会读取该文件。

## 5. .env 安全说明

`.env.example` 只放示例值。真实 `.env` 可能包含模型 API Key，禁止提交。

注意：部分 Docker Compose 版本执行 `docker compose config` 时会展开 `.env` 中的变量。不要把包含真实密钥的命令输出直接粘贴到公开 Issue、文档或截图中。

建议公开仓库前检查：

```bash
git status --short
```

确认没有 `.env`、`data/*.db`、日志、虚拟环境或 `node_modules`。

## 6. 常见错误排查

### 6.1 前端启动找不到 package.json

请从项目根目录执行：

```powershell
.\scripts\run_frontend.ps1
```

脚本会根据自身路径定位 `frontend/package.json`，如果路径异常会直接报错。

### 6.2 后端提示 OPENAI_API_KEY 未配置

检查 `.env`：

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://example-openai-compatible-endpoint/v1
OPENAI_MODEL=your-model-name
```

修改后重启后端。

### 6.3 `/api/ready` 返回 503

`/api/ready` 会检查模型 Key、会话库和 checkpoint 目录。根据返回的 `checks` 字段排查。

### 6.4 PowerShell 无法运行 npm

如果 `npm run ...` 被执行策略拦截，可以使用：

```powershell
npm.cmd run test
npm.cmd run typecheck
npm.cmd run build
```

### 6.5 Graphviz 本地不可用

本地没有 Graphviz 时，图表能力会返回 DOT 源码。安装 Graphviz 后确保 `dot` 命令在 PATH 中。

Docker 后端镜像已安装 Graphviz，不需要额外安装。

### 6.6 Docker 前端无法访问后端

前端容器中的 Nginx 将 `/api/` 反向代理到 `http://backend:8010/api/`。如果接口不可用，先检查：

```bash
docker compose ps
docker compose logs backend
docker compose logs frontend
```

### 6.7 多 worker 问题

项目使用 SQLite checkpoint，后端保持 `workers=1`。Compose 中已设置：

```yaml
UVICORN_WORKERS: "1"
WEB_CONCURRENCY: "1"
```

## 7. 验证命令

```powershell
.\.venv\Scripts\python.exe -m pytest tests/backend tests/agent/test_safe_trace.py tests/agent/test_capability_catalog.py tests/agent/test_routing.py tests/agent/test_golden_routes.py -q --no-cov
```

```powershell
cd frontend
npm run test
npm run typecheck
npm run build
```

```bash
docker compose config
docker compose build
```
