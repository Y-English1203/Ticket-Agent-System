import sqlite3
import json
from datetime import datetime
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")

# ============ 工具函数 ============
def create_ticket(user_id: str, issue: str, priority: str = "中") -> str:
    conn = sqlite3.connect("tickets.db")
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO tickets (user_id, issue, priority, created_at, updated_at) VALUES (?,?,?,?,?)",
        (user_id, issue, priority, now, now)
    )
    ticket_id = cursor.lastrowid
    cursor.execute(
        "INSERT INTO audit_log (ticket_id, action, operator, timestamp) VALUES (?,?,?,?)",
        (ticket_id, "创建工单", "AI", now)
    )
    conn.commit()
    conn.close()
    return f"工单已创建，编号：{ticket_id}，优先级：{priority}，问题：{issue}"

def check_ticket_status(ticket_id: int) -> str:
    conn = sqlite3.connect("tickets.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, issue, priority, status, handler FROM tickets WHERE id=?", (ticket_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return f"未找到编号为 {ticket_id} 的工单"
    return f"工单 {row[0]}：{row[1]}，优先级：{row[2]}，当前状态：{row[3]}，处理人：{row[4]}"

def list_user_tickets(user_id: str) -> str:
    conn = sqlite3.connect("tickets.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, issue, status FROM tickets WHERE user_id=?", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    if not rows:
        return f"用户 {user_id} 暂无工单"
    result = "\n".join([f"工单 {r[0]}：{r[1]}，状态：{r[2]}" for r in rows])
    return f"用户 {user_id} 的工单列表：\n{result}"

def escalate_to_human(ticket_id: int, reason: str) -> str:
    conn = sqlite3.connect("tickets.db")
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "UPDATE tickets SET status='待人工审批', handler='人工', updated_at=? WHERE id=?",
        (now, ticket_id)
    )
    cursor.execute(
        "INSERT INTO audit_log (ticket_id, action, operator, timestamp) VALUES (?,?,?,?)",
        (ticket_id, f"转人工：{reason}", "AI", now)
    )
    conn.commit()
    conn.close()
    return f"工单 {ticket_id} 已转人工处理，原因：{reason}，请等待人工客服联系。"

# ============ 工具定义 ============
tools = [
    {
        "type": "function",
        "function": {
            "name": "create_ticket",
            "description": "当用户描述了一个新问题需要处理时，创建工单",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "用户ID"},
                    "issue": {"type": "string", "description": "问题描述"},
                    "priority": {"type": "string", "enum": ["低", "中", "高"], "description": "优先级"}
                },
                "required": ["user_id", "issue"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_ticket_status",
            "description": "查询某个工单的当前状态",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticket_id": {"type": "integer", "description": "工单编号"}
                },
                "required": ["ticket_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_user_tickets",
            "description": "列出某个用户的所有工单",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "用户ID"}
                },
                "required": ["user_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "escalate_to_human",
            "description": "当问题涉及退款、投诉、纠纷等敏感操作时，转人工处理",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticket_id": {"type": "integer", "description": "工单编号"},
                    "reason": {"type": "string", "description": "转人工原因"}
                },
                "required": ["ticket_id", "reason"]
            }
        }
    }
]

# ============ Agent 主循环 ============
def run_agent(user_input: str, user_id: str = "user_001") -> str:
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": f"你是一个企业客服工单助手。当前用户ID是 {user_id}。请根据用户的问题，调用合适的工具处理。"},
            {"role": "user", "content": user_input}
        ],
        tools=tools,
        tool_choice="auto"
    )

    message = response.choices[0].message
    if not message.tool_calls:
        return message.content

    tool_call = message.tool_calls[0]
    function_name = tool_call.function.name
    args = json.loads(tool_call.function.arguments)

    if function_name == "create_ticket":
        return create_ticket(args.get("user_id", user_id), args["issue"], args.get("priority", "中"))
    elif function_name == "check_ticket_status":
        return check_ticket_status(args["ticket_id"])
    elif function_name == "list_user_tickets":
        return list_user_tickets(args.get("user_id", user_id))
    elif function_name == "escalate_to_human":
        return escalate_to_human(args["ticket_id"], args["reason"])
    else:
        return "未知的工具调用"

if __name__ == "__main__":
    print(run_agent("我要投诉，订单迟迟不发货，请帮我处理"))
    print(run_agent("查看我所有的工单"))
    print(run_agent("工单1现在什么状态"))