## 主な機能

1. **Gmail (IMAP) からのアラートメール取得**
   - アプリパスワード方式の IMAP 接続により、特定ラベル（`01.日々の情報収集/01.03GoogleScholar`）のメールを新しい順から過去へ遡って取得します。
2. **ローカル HTML 解析と原題による重複スキップ**
   - Google Scholar アラートメールの HTML をローカルで解析し、Notion に登録済みの論文（原題照合）は API 枠を消費せずに自動スキップします。
   - 1回の実行あたり未登録の論文が `MAX_PAPERS_PER_RUN`（既定: 20件）登録できるまで過去のメールを遡ります。
3. **AI による日本語要約・解説・新規性図解の生成**
   - デフォルトで **Gemini API（`gemini-3-flash-preview`）** を使用し、`USE_GEMINI=false` で **Claude API（`claude-sonnet-4-6`）** に切り替え可能です。
   - 日本語タイトル、要約、一言キャッチコピー、取り組んだ問題、新規性の説明、大学1年生向けの解説、および新規性にフォーカスした図解ステップを生成します。
4. **論文 PDF からの Git リポジトリ URL 抽出**
   - 論文の PDF が取得可能な場合、本文テキストから著者の GitHub / GitLab / Bitbucket リポジトリ URL を自動抽出します。
5. **Notion データベースへの登録**
   - 対象データベースのスキーマを動的に取得し、タイトル・原題・著者・掲載誌・日付（実行日・JST）・PDF/DOI/Git リンクおよび本文ブロックを登録します。
6. **最初の1件の要約を新規 Git ブランチ（`README.pdf` / `README.md`）として出力**
   - 各実行で最初に登録された論文について、新規性の図解を含む要約を `README.pdf` および `README.md`（Mermaid フローチャート付き）として生成し、`paper/YYYYMMDD-論文タイトルスラグ` ブランチへ自動でコミット＆push します。

---

## 実行方法

### ローカル実行

Python 3.10 以上および [`uv`](https://docs.astral.sh/uv/) を使用します。

```bash
# 依存関係のインストール
uv sync

# パイプラインの実行
uv run python scholar_to_notion.py
```

### GitHub Actions による定期実行

[`.github/workflows/main.yml`](.github/workflows/main.yml) により、毎日 **JST 09:00（UTC 00:00）** に自動実行されます（`workflow_dispatch` による手動実行も可能）。

---

## 環境変数（`.env` / GitHub Actions Secrets）

`.env.example` をコピーして `.env` を作成し、以下の変数を設定してください（GitHub Actions では Repository secrets に登録）。

| 変数名 | 必須 | 説明 |
|---|---|---|
| `GEMINI_API_KEY` | ○（デフォルト時） | Google AI Studio で発行した Gemini API キー |
| `ANTHROPIC_API_KEY` | `USE_GEMINI=false` 時 | Anthropic Console で発行した Claude API キー |
| `NOTION_TOKEN` | ○ | Notion Integration トークン |
| `GMAIL_USER` | ○ | 対象の Gmail / Google Workspace アドレス |
| `GMAIL_APP_PASSWORD` | ○ | Google アカウントのアプリパスワード（16文字） |
| `USE_GEMINI` | 任意（既定: `true`） | `true` で Gemini API、`false` で Claude API を使用 |
| `GEMINI_MODEL` | 任意（既定: `gemini-3-flash-preview`） | 使用する Gemini モデル名 |
| `MAX_PAPERS_PER_RUN` | 任意（既定: `20`） | 1回の実行で新規登録する未登録論文の上限数 |
| `DEBUG` | 任意（既定: `false`） | `true` の場合は最新 `DEBUG_THREAD_LIMIT` スレッドのみ処理し、`debug/` に中間成果物を保存 |

---

## モジュール構成

| ファイル | 役割 |
|---|---|
| `scholar_to_notion.py` | エントリポイント。パイプライン全体を統括 |
| `config.py` | 定数と環境変数のロード |
| `gmail.py` | Gmail IMAP 接続・ラベル解決・過去スレッドのバッチ走査・本文取得 |
| `ai.py` | Scholar HTML のローカル解析、および Gemini / Claude API による日本語解説・図解データの生成 |
| `pdf.py` | 論文 PDF の取得・Git URL 抽出・日本語要約 PDF（`README.pdf`）の生成 |
| `git_publish.py` | 要約 Markdown（`README.md`）の生成と新規 Git ブランチへの `README.pdf` / `README.md` 登録・push |
| `notion.py` | Notion データベースのスキーマ取得・原題による重複判定・ページ作成 |
| `history.md` | 主な変更履歴・トラブルシューティング記録 |
