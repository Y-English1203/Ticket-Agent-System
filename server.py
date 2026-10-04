import os
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from ticket_graph import ticket_agent, TicketState

load_dotenv()

app = FastAPI(title="企业客服工单 Agent 系统")

class Question(BaseModel):
    question: str
    user_id: str = "user_001"

@app.get("/")
def root():
    return {"message": "企业客服工单 Agent 系统已启动"}

@app.post("/ask/ticket")
def ask_ticket(q: Question):
    """客服工单 Agent 接口（基于 LangGraph 状态机）"""
    initial_state: TicketState = {
        "user_id": q.user_id,
        "user_input": q.question,
        "intent": "",
        "ticket_id": 0,
        "is_sensitive": False,
        "need_human": False,
        "reply": "",
        "history": []
    }
    result = ticket_agent.invoke(initial_state)
    return {
        "answer": result["reply"],
        "intent": result["intent"],
        "need_human": result["need_human"]
    }