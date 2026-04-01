"""
retriever.py
線上階段：接收使用者查詢，透過圖譜找到最相關的 SOP
"""

import json
import anthropic

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-20250514"


def _call_claude(system_prompt: str, user_content: str) -> str:
    response = client.messages.create(
        model=MODEL,
        max_tokens=500,
        system=system_prompt,
        messages=[{"role": "user", "content": user_content}]
    )
    return response.content[0].text


# ──────────────────────────────────────────
# Step 1：LLM 路由器（判斷查詢意圖）
# ──────────────────────────────────────────

def llm_router(query: str) -> dict:
    """判斷查詢偏向哪種圖譜，回傳權重"""
    system = """你是 SOP 查詢意圖分析專家。
分析使用者查詢，輸出三個圖譜的權重（總和為 1.0）：
- wE (實體圖)：查詢包含具體設備名稱、告警碼、參數數值
- wC (因果圖)：查詢在問「為什麼」、「什麼原因」、診斷問題
- wF (流程圖)：查詢在問「怎麼做」、「步驟是什麼」、要處理方法

只輸出 JSON，不要有其他文字：
{"wE": 0.x, "wC": 0.x, "wF": 0.x}"""

    raw = _call_claude(system, f"查詢：{query}")
    weights = json.loads(raw.strip())
    print(f"  路由器權重 → 實體:{weights['wE']} 因果:{weights['wC']} 流程:{weights['wF']}")
    return weights


# ──────────────────────────────────────────
# Step 2：各圖譜評分函數
# ──────────────────────────────────────────

def entity_score(query: str, graph_data: dict) -> float:
    """計算查詢與實體圖的相關度（關鍵字重疊）"""
    query_lower = query.lower()
    entities = graph_data.get("entity_graph", {}).get("entities", [])

    if not entities:
        return 0.0

    hits = 0
    for entity in entities:
        name = entity.get("name", "").lower()
        desc = entity.get("description", "").lower()
        if name in query_lower or any(word in query_lower for word in name.split()):
            hits += 1
        elif any(word in desc for word in query_lower.split() if len(word) > 1):
            hits += 0.3

    return min(hits / max(len(entities), 1), 1.0)


def causal_score(query: str, graph_data: dict) -> float:
    """計算查詢與因果圖的相關度"""
    query_lower = query.lower()
    relations = graph_data.get("causal_graph", {}).get("causal_relations", [])

    if not relations:
        return 0.0

    hits = 0
    for rel in relations:
        from_node = rel.get("from", "").lower()
        to_node = rel.get("to", "").lower()
        combined = f"{from_node} {to_node}"
        if any(word in combined for word in query_lower.split() if len(word) > 1):
            hits += 1

    return min(hits / max(len(relations), 1), 1.0)


def flow_score(query: str, graph_data: dict) -> float:
    """計算查詢與流程圖的相關度"""
    query_lower = query.lower()
    steps = graph_data.get("flow_graph", {}).get("steps", [])

    if not steps:
        return 0.0

    hits = 0
    for step in steps:
        desc = step.get("description", "").lower()
        if any(word in desc for word in query_lower.split() if len(word) > 1):
            hits += 1

    return min(hits / max(len(steps), 1), 1.0)


def pc_score(query: str, graph_data: dict) -> float:
    """計算查詢與程序卡的相關度（標題 + 摘要）"""
    query_lower = query.lower()
    pc = graph_data.get("procedure_card", {})
    title = pc.get("title", "").lower()
    abstract = pc.get("abstract", "").lower()
    combined = f"{title} {abstract}"

    words = [w for w in query_lower.split() if len(w) > 1]
    if not words:
        return 0.0

    hits = sum(1 for w in words if w in combined)
    return hits / len(words)


# ──────────────────────────────────────────
# Step 3：主檢索函數
# ──────────────────────────────────────────

def retrieve(query: str, all_graphs: list, top_k: int = 3, lambda_: float = 0.5) -> list:
    """
    主檢索：結合程序卡篩選 + 路由器 + 三圖評分
    回傳 top_k 個最相關的 SOP
    """
    # 路由器判斷意圖權重
    weights = llm_router(query)
    wE = weights.get("wE", 0.33)
    wC = weights.get("wC", 0.33)
    wF = weights.get("wF", 0.34)

    results = []
    for graph_data in all_graphs:
        sop_id = graph_data.get("sop_id", "unknown")

        # 各項評分
        s_pc     = pc_score(query, graph_data)
        s_entity = entity_score(query, graph_data)
        s_causal = causal_score(query, graph_data)
        s_flow   = flow_score(query, graph_data)

        # 加權總分（對應論文公式 6）
        expert_score = wE * s_entity + wC * s_causal + wF * s_flow
        final_score  = lambda_ * s_pc + (1 - lambda_) * expert_score

        results.append({
            "sop_id":       sop_id,
            "final_score":  round(final_score, 4),
            "pc_score":     round(s_pc, 4),
            "entity_score": round(s_entity, 4),
            "causal_score": round(s_causal, 4),
            "flow_score":   round(s_flow, 4),
            "graph_data":   graph_data
        })

    # 依分數排序，回傳 Top-K
    results.sort(key=lambda x: x["final_score"], reverse=True)
    return results[:top_k]
