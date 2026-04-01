"""
main.py
主程式：整合離線建圖 + 線上查詢的完整 Demo
"""

import os
import json
import sys
from dotenv import load_dotenv

# 載入 .env 檔
load_dotenv()

# 把 src 加入路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.graph_builder import build_all_graphs
from src.retriever import retrieve
from src.generator import generate_response

# ──────────────────────────────────────────
# 設定
# ──────────────────────────────────────────

SOP_DIR    = os.path.join(os.path.dirname(__file__), "data", "sops")
GRAPH_DIR  = os.path.join(os.path.dirname(__file__), "graphs")
os.makedirs(GRAPH_DIR, exist_ok=True)


# ──────────────────────────────────────────
# 離線階段：建立圖譜並存檔
# ──────────────────────────────────────────

def offline_build():
    """讀取所有 SOP 文件，建立圖譜並存成 JSON"""
    sop_files = [f for f in os.listdir(SOP_DIR) if f.endswith(".txt")]
    print(f"\n{'='*50}")
    print(f"【離線階段】找到 {len(sop_files)} 份 SOP 文件")
    print(f"{'='*50}")

    all_graphs = []
    for filename in sop_files:
        sop_id   = filename.replace(".txt", "")
        sop_path = os.path.join(SOP_DIR, filename)
        save_path = os.path.join(GRAPH_DIR, f"{sop_id}.json")

        # 如果已經建好圖譜，直接載入，不重複呼叫 API
        if os.path.exists(save_path):
            print(f"\n[載入快取] {sop_id}")
            with open(save_path, "r", encoding="utf-8") as f:
                graph_data = json.load(f)
        else:
            print(f"\n[建立圖譜] {sop_id}")
            with open(sop_path, "r", encoding="utf-8") as f:
                sop_text = f.read()

            graph_data = build_all_graphs(sop_id, sop_text)

            # 存檔（下次直接載入，不重複呼叫 API）
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(graph_data, f, ensure_ascii=False, indent=2)
            print(f"  ✓ 已存檔：{save_path}")

        all_graphs.append(graph_data)

    return all_graphs


# ──────────────────────────────────────────
# 線上階段：使用者查詢
# ──────────────────────────────────────────

def online_query(query: str, all_graphs: list):
    """接收查詢，執行檢索 + 生成"""
    print(f"\n{'='*50}")
    print(f"【線上查詢】{query}")
    print(f"{'='*50}")

    # Step 1 + 2 + 3：檢索（路由器 + 三圖評分）
    print("\n▶ 檢索中...")
    results = retrieve(query, all_graphs, top_k=3)

    # 顯示檢索結果排名
    print("\n  檢索排名：")
    for i, r in enumerate(results):
        pc_title = r["graph_data"].get("procedure_card", {}).get("title", r["sop_id"])
        print(f"  #{i+1} [{r['sop_id']}] {pc_title}")
        print(f"      總分:{r['final_score']} | PC:{r['pc_score']} "
                f"實體:{r['entity_score']} 因果:{r['causal_score']} 流程:{r['flow_score']}")

    # Step 4：取最佳 SOP 生成回答
    best = results[0]
    print(f"\n▶ 使用最佳 SOP 生成回答...")
    answer = generate_response(query, best)

    print(f"\n{'='*50}")
    print("【AI 回答】")
    print(f"{'='*50}")
    print(answer)

    return answer


# ──────────────────────────────────────────
# 主程式
# ──────────────────────────────────────────

def main():
    # 檢查 API Key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("❌ 請先設定 ANTHROPIC_API_KEY 環境變數")
        print("   export ANTHROPIC_API_KEY='your-key-here'")
        sys.exit(1)

    # 離線建圖
    all_graphs = offline_build()

    # 測試查詢
    test_queries = [
        # "伺服器溫度過高，ALARM-TEMP-001 被觸發，我該怎麼辦？",
        # "為什麼伺服器會過熱？",
        "伺服器連不上，該如何排查？",
    ]

    for query in test_queries:
        online_query(query, all_graphs)
        print("\n" + "─" * 50 + "\n")


if __name__ == "__main__":
    main()
