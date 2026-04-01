"""
generator.py
線上階段：拿到最佳 SOP 的流程圖，生成可執行的回答
"""

import anthropic

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-20250514"


def linearize_flow(flow_graph: dict) -> str:
    """把流程圖（JSON）轉成人類可讀的步驟文字"""
    steps = flow_graph.get("steps", [])
    if not steps:
        return "（無步驟資料）"

    lines = []
    for step in steps:
        sid  = step.get("id", "")
        desc = step.get("description", "")
        lines.append(f"• {sid}: {desc}")

        # 有條件分支的話一併顯示
        for cond in step.get("conditions", []):
            condition = cond.get("condition", "")
            next_step = cond.get("next", "")
            lines.append(f"    → {condition}：前往 {next_step}")

    return "\n".join(lines)


def generate_response(query: str, best_result: dict) -> str:
    """
    用最佳 SOP 的流程圖 + 使用者問題，生成可執行回答
    這是線上階段的第二次 LLM 呼叫
    """
    graph_data = best_result.get("graph_data", {})
    sop_id     = best_result.get("sop_id", "未知")

    # 取出程序卡和流程圖
    pc         = graph_data.get("procedure_card", {})
    flow_graph = graph_data.get("flow_graph", {})

    sop_title    = pc.get("title", sop_id)
    linearized   = linearize_flow(flow_graph)

    system = """你是工業操作助理。
根據提供的 SOP 步驟回答操作員的問題。

規則：
1. 只能使用 SOP 步驟中的內容，不可自行補充或發明步驟
2. 回答要清楚、簡潔、可直接照做
3. 用繁體中文回答
4. 格式：先說明對應的 SOP 名稱，再列出步驟"""

    user_content = f"""操作員問題：{query}

對應 SOP：{sop_title}

SOP 執行步驟：
{linearized}

請根據以上步驟回答操作員的問題。"""

    response = client.messages.create(
        model=MODEL,
        max_tokens=1000,
        system=system,
        messages=[{"role": "user", "content": user_content}]
    )

    return response.content[0].text
