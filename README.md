# LLM-SOP Demo
SOPRAG 論文的最小可跑實作，使用 Claude (Anthropic) 作為 LLM。

## 專案結構
```
LLM-SOP/
├── main.py                  # 主程式入口
├── requirements.txt
├── src/
│   ├── graph_builder.py     # 離線建圖（實體圖、因果圖、流程圖）
│   ├── retriever.py         # 線上檢索（路由器 + 三圖評分）
│   └── generator.py         # 線上生成（流程圖 → 回答）
├── data/
│   └── sops/                # 放你的 SOP .txt 文件
└── graphs/                  # 自動產生的圖譜 JSON（快取）
```

## 快速開始

### 1. 建立虛擬環境
```bash
python -m venv venv
source venv/bin/activate      # Mac/Linux
# venv\Scripts\activate       # Windows
```

### 2. 安裝套件
```bash
pip install -r requirements.txt
```

### 3. 設定 API Key
```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```

### 4. 執行
```bash
python main.py
```

## 新增你自己的 SOP
把 SOP 文字存成 `.txt` 放入 `data/sops/` 資料夾，再執行 `main.py` 即可。

## 流程說明
```
【離線階段】（只跑一次，結果快取在 graphs/）
SOP 文件 → 程序卡 + 實體圖 + 因果圖 + 流程圖 → 存成 JSON

【線上階段】（每次查詢）
使用者問題
  → ① 程序卡評分篩選
  → ② LLM 路由器（判斷意圖，分配權重）
  → ③ 三圖加權評分，找到最佳 SOP
  → ④ 流程圖線性化 + 生成回答
```
