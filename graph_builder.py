"""
graph_builder.py
離線階段：讀取 SOP 文字，呼叫 Claude 建立三種圖譜
"""

import json
import anthropic

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-20250514"


def _call_claude(system_prompt: str, user_content: str) -> str:
    """共用的 Claude 呼叫函數"""
    response = client.messages.create(
        model=MODEL,
        max_tokens=2000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_content}]
    )
    return response.content[0].text


# ──────────────────────────────────────────
# 1. 程序卡（Procedure Card）
# ──────────────────────────────────────────

def build_procedure_card(sop_text: str) -> dict:
    """產生程序卡：只有標題 + 一句摘要"""
    system = """你是 SOP 分析專家。
請從 SOP 文件中擷取：
1. title: 此程序的主要功能標題（15字以內）
2. abstract: 一句話說明此程序的目的與觸發時機（30字以內）

只輸出 JSON，格式如下，不要有其他文字：
{"title": "...", "abstract": "..."}"""

    raw = _call_claude(system, sop_text)
    return json.loads(raw.strip())


# ──────────────────────────────────────────
# 2. 實體圖（Entity Graph）
# ──────────────────────────────────────────

def build_entity_graph(sop_text: str) -> dict:
    """提取 SOP 中的關鍵實體"""
    system = """你是 SOP 實體擷取專家。
從 SOP 中提取以下類型的實體：
- alarm: 告警碼（如 ALARM-TEMP-001）
- equipment: 設備/資產（如 DCIM、iDRAC、風扇）
- parameter: 參數（如 溫度35°C、CPU 85°C）
- role: 角色（如 機房主管、網路管理員）
- document: 文件（如 ILF-01）

只輸出 JSON，格式如下，不要有其他文字：
{
  "entities": [
    {"name": "實體名稱", "type": "類型", "description": "簡短說明"}
  ]
}"""

    raw = _call_claude(system, sop_text)
    return json.loads(raw.strip())


# ──────────────────────────────────────────
# 3. 因果圖（Causal Graph）
# ──────────────────────────────────────────

def build_causal_graph(sop_text: str) -> dict:
    """提取 SOP 中的因果關係"""
    system = """你是 SOP 因果關係擷取專家。
從 SOP 中找出所有因果關係，關係類型包括：
- CAUSES: A 導致 B
- PREVENTS: A 阻止 B
- TRIGGERS: A 觸發 B
- RESULTS_IN: A 的結果是 B

只輸出 JSON，格式如下，不要有其他文字：
{
  "causal_relations": [
    {"from": "原因", "relation": "CAUSES", "to": "結果"}
  ]
}"""

    raw = _call_claude(system, sop_text)
    return json.loads(raw.strip())


# ──────────────────────────────────────────
# 4. 流程圖（Flow Graph）
# ──────────────────────────────────────────

def build_flow_graph(sop_text: str) -> dict:
    """提取 SOP 的執行步驟流程"""
    system = """你是 SOP 流程擷取專家。
從 SOP 中提取執行步驟，注意：
- 每個步驟要有 id、description
- 若有條件分支，用 conditions 表示
- 不要加入「開始」或「結束」節點

只輸出 JSON，格式如下，不要有其他文字：
{
  "steps": [
    {
      "id": "step_1",
      "description": "步驟描述",
      "next": ["step_2"],
      "conditions": [
        {"condition": "若 X 成立", "next": "step_3"}
      ]
    }
  ]
}"""

    raw = _call_claude(system, sop_text)
    return json.loads(raw.strip())


# ──────────────────────────────────────────
# 主函數：一次建立所有圖譜
# ──────────────────────────────────────────

def build_all_graphs(sop_id: str, sop_text: str) -> dict:
    """對一份 SOP 建立全部四種結構"""
    print(f"  [1/4] 建立程序卡...")
    pc = build_procedure_card(sop_text)

    print(f"  [2/4] 建立實體圖...")
    entity = build_entity_graph(sop_text)

    print(f"  [3/4] 建立因果圖...")
    causal = build_causal_graph(sop_text)

    print(f"  [4/4] 建立流程圖...")
    flow = build_flow_graph(sop_text)

    return {
        "sop_id": sop_id,
        "raw_text": sop_text,
        "procedure_card": pc,
        "entity_graph": entity,
        "causal_graph": causal,
        "flow_graph": flow
    }
