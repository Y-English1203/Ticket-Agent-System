import os
from typing import TypedDict, Literal
from dotenv import load_dotenv
from openai import OpenAI
from langgraph.graph import StateGraph, END
from ticket_agent import create_ticket, check_ticket_status, list_user_tickets, escalate_to_human

load_dotenv()
client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")

class TicketState(TypedDict):
    user_id: str
    user_input: str
    intent: str          # create / query / complaint
    ticket_id: int
    is_sensitive: bool   # 是否敏感操作
    need_human: bool     # 是否需要人工审批
    reply: str
    history: list

def classify_intent(state: TicketState) -> TicketState:
    """判断用户意图"""
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{
            "role": "user",
            "content": f"判断用户意图，只回答一个词：create（创建工单）、query（查询工单）、complaint（投诉/退款等敏感问题）。\n\n用户：{state['user_input']}"
        }],
        temperature=0
    )
    state["intent"] = response.choices[0].message.content.strip().lower()
    return state

def handle_create(state: TicketState) -> TicketState:
    """处理创建工单"""
    result = create_ticket(state["user_id"], state["user_input"])
    state["reply"] = result
    return state

def handle_query(state: TicketState) -> TicketState:
    """处理查询工单"""
    result = list_user_tickets(state["user_id"])
    state["reply"] = result
    return state

def handle_complaint(state: TicketState) -> TicketState:
    """处理投诉：先创建工单，再判断是否转人工"""
    result = create_ticket(state["user_id"], state["user_input"], priority="高")
    state["reply"] = result
    state["is_sensitive"] = True
    return state

def human_approval(state: TicketState) -> TicketState:
    """人工审批节点（模拟：自动通过，但记录日志）"""
    state["reply"] += "\n[系统] 该工单已进入人工审批流程，人工客服将在2小时内联系您。"
    state["need_human"] = True
    return state

def route_after_classify(state: TicketState) -> str:
    if "complaint" in state["intent"]:
        return "handle_complaint"
    elif "query" in state["intent"]:
        return "handle_query"
    else:
        return "handle_create"

def route_after_complaint(state: TicketState) -> str:
    return "human_approval" if state["is_sensitive"] else "end"

def build_ticket_graph():
    graph = StateGraph(TicketState)
    graph.add_node("classify_intent", classify_intent)
    graph.add_node("handle_create", handle_create)
    graph.add_node("handle_query", handle_query)
    graph.add_node("handle_complaint", handle_complaint)
    graph.add_node("human_approval", human_approval)

    graph.set_entry_point("classify_intent")
    graph.add_conditional_edges("classify_intent", route_after_classify, {
        "handle_create": "handle_create",
        "handle_query": "handle_query",
        "handle_complaint": "handle_complaint"
    })
    graph.add_edge("handle_create", END)
    graph.add_edge("handle_query", END)
    graph.add_conditional_edges("handle_complaint", route_after_complaint, {
        "human_approval": "human_approval",
        "end": END
    })
    graph.add_edge("human_approval", END)

    return graph.compile()

ticket_agent = build_ticket_graph()