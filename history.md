## 2026-10-26: Gemini API / Claude API の切り替え対応（デフォルト: Gemini API）

`ai.py` および関連ファイルにフラグを追加し、デフォルトで Gemini API（`gemini-2.5-flash`）、フラグ切り替えで Claude API を使用できるように対応。

### 主な変更点

1. **`config.py`**
   - `GEMINI_MODEL`（デフォルト: `"gemini-2.5-flash"`、環境変数 `GEMINI_MODEL` で上書き可）を追加
   - `USE_GEMINI`（デフォルト: `True`、環境変数 `USE_GEMINI=false` で Claude に切り替え可）を追加

2. **`ai.py`**
   - `_complete_json_gemini`: `requests` を使って Gemini REST API（`generateContent`、`responseMimeType="application/json"`）を直接呼び出す処理を追加
   - `_complete_json_claude`: 既存の Claude API 呼び出し処理を分離（`client=None` の場合は `ANTHROPIC_API_KEY` から自動初期化）
   - `_complete_json` / `extract_papers_with_claude` / `generate_japanese_content`: キーワード引数 `use_gemini: bool = USE_GEMINI` を追加し、設定値または呼び出し単位のフラグで切り替え可能に更新

3. **`scholar_to_notion.py` / `.env.example` / `.github/workflows/main.yml`**
   - `_require_env` と `main` を `USE_GEMINI` に連動させ、Gemini 使用時は `GEMINI_API_KEY`、Claude 使用時は `ANTHROPIC_API_KEY` をチェックするよう更新

### 使い方
- **Gemini API を使う場合（デフォルト）**: `.env` に `GEMINI_API_KEY=...` を設定して実行
- **Claude API に切り替える場合**: 環境変数 `USE_GEMINI=false`（または `config.py` の `USE_GEMINI = False`）を設定して実行
