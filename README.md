# 企业客服工单 Agent 系统

基于 LangGraph + Function Calling 构建的企业级客服 Agent，支持自然语言创建工单、查询进度、转人工等操作，覆盖客服场景的完整业务流程。

## 核心功能

- **多工具调用**：Agent 可自主调用 `create_ticket`（创建工单）、`check_ticket_status`（查询状态）、`list_user_tickets`（列出工单）、`escalate_to_human`（转人工）四个工具。
- **意图识别路由**：通过 Function Calling 让大模型根据用户问题自主决策调用哪个工具，无需手动选择。
- **人工审批机制**：涉及退款、投诉等敏感操作时，Agent 自动转人工处理，确保流程可控。
- **审计日志**：每步操作记录时间、操作人、变更内容，便于追溯。
- **状态管理**：基于 SQLite 实现工单状态流转（待处理 → 待人工审批 → 已解决）。

## 技术栈

Python、LangGraph、FastAPI、SQLite、Function Calling、DeepSeek API、python-dotenv

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```
### 初始化数据库
```bash
python init_ticket_db.py
```
### 启动服务

```bash
uvicorn server:app --port 8001
```