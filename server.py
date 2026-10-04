import os
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from ticket_agent import run_agent

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
    """客服工单 Agent 接口：支持创建工单、查询状态、列出工单、转人工"""
    answer = run_agent(q.question, user_id=q.user_id)
    return {"answer": answer}