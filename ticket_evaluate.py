import json
import requests
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")

with open("ticket_eval_set.json", "r", encoding="utf-8") as f:
    eval_set = json.load(f)

hit = 0
for item in eval_set:
    r = requests.post("http://127.0.0.1:8001/ask/ticket", json={"question": item["question"], "user_id": "eval_user"})
    answer = r.json().get("answer", "")
    judge = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": f"判断以下回答是否覆盖了这些关键词：{item['expected_keywords']}。只回答'是'或'否'。\n\n回答：{answer}"}],
        temperature=0
    )
    passed = "是" in judge.choices[0].message.content.strip()
    if passed:
        hit += 1
    print(f"[{'✓' if passed else '✗'}] {item['question']}")

print(f"\n命中率：{hit}/{len(eval_set)} = {hit/len(eval_set)*100:.1f}%")