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

---

## 2026-10-26: GitHub Actions 実行時の警告・通知メッセージと対処について

GitHub Actions 実行時に Summary 画面に表示される以下の2件のメッセージは、パイプライン自体のエラーではなく **警告・通知（Annotations）**。

### 1. 表示されたメッセージの意味
1. **`Node.js 20 is deprecated... (actions/checkout@v4, astral-sh/setup-uv@v5)`**
   - `.github/workflows/main.yml` で指定している Action のバージョン（`actions/checkout@v4`、`astral-sh/setup-uv@v5`）が古い Node.js 20 向けのため、GitHub Actions 側で強制的に Node.js 24 で実行しているという警告。
   - `actions/checkout@v5` および新しい `astral-sh/setup-uv` に上げることで解消可能。

2. **`The ubuntu-latest label will migrate to Ubuntu 26...`**
   - `.github/workflows/main.yml` の `runs-on: ubuntu-latest` に対して、Ubuntu 26 への移行期間中に出る GitHub からの案内通知。
   - そのままでも動作するが、`runs-on: ubuntu-24.04` のようにバージョンを明示すると通知が出なくなる。

### 2. ジョブ自体が Failed になる場合の注意点
デフォルトを Gemini API に変更したため、GitHub リポジトリの **Settings → Secrets and variables → Actions** に **`GEMINI_API_KEY`** が未登録だと、`Run Scholar → Notion pipeline` ステップ内の `_require_env` で以下のエラーになって終了する。
```text
Missing environment variables: GEMINI_API_KEY
```
- **Gemini を使う場合**: GitHub リポジトリの Actions secrets に `GEMINI_API_KEY` を追加する。
- **Claude を使う場合**: Actions secrets に `USE_GEMINI` = `false` を追加する。

---

## 2026-10-26: GitHub Actions で未設定の Secret が空文字になり Claude 側にフォールバックする問題の修正

### 原因
GitHub Actions では、`.github/workflows/main.yml` の `USE_GEMINI: ${{ secrets.USE_GEMINI }}` に対して Secret が未登録の場合、環境変数 `USE_GEMINI` が未定義（`None`）ではなく **空文字列（`""`）** として渡される。

従来の `config.py` の `_env_bool` は `raw is None` のときだけ `default`（`True`）を返していたため、空文字列 `""` が `False` と判定されて Claude API 側に切り替わり、Anthropic のクレジット残高不足エラー（`Your credit balance is too low to access the Anthropic API`）が発生していた。
（同様に `DEBUG` も GitHub Secrets 未設定時は空文字列となり `False` と判定されていた。）

### 修正内容
- `.github/workflows/main.yml` の警告解消:
  - `runs-on`: `ubuntu-latest` → `ubuntu-24.04`（Ubuntu 26 移行通知を回避）
  - `actions/checkout`: `v4` → `v6`（Node.js 24 対応版）
  - `astral-sh/setup-uv`: `v5` → `v9.0.0`（Node.js 24 対応版）
- `config.py` の `_env_bool` で、未設定（`None`）だけでなく **空文字列（`not raw.strip()`）の場合も `default` 値を返す**ように修正。
  - これにより、GitHub Secrets に `USE_GEMINI` を設定しなくてもデフォルトの `True`（Gemini API）がそのまま使われる。

---

## 2026-10-26: Gemini API で `gemini-2.5-flash` が 404 Not Found になる問題の修正

### 原因
Google AI Studio / Gemini API では、新規作成されたプロジェクトや API キーに対して旧世代モデル（`gemini-2.5-flash` 等）へのアクセスが制限されており、`404 Not Found`（`This model models/gemini-2.5-flash is no longer available to new users`）が返される仕様になっている。

### 修正内容
1. **`config.py`**
   - デフォルトの `GEMINI_MODEL` を最新世代の `"gemini-3-flash-preview"` に更新（環境変数 `GEMINI_MODEL` が空文字の場合もデフォルト値にフォールバック）。
2. **`ai.py`**
   - `_complete_json_gemini` で、指定モデルが `404` を返した場合に自動でフォールバック候補（`gemini-3-flash-preview` → `gemini-3.1-flash-lite-preview` → `gemini-2.5-flash` 等）を順に試行する処理を追加。
   - 候補がすべて `404` の場合は `_discover_gemini_model` で `GET /v1beta/models`（モデル一覧 API）を叩き、その API キーで `generateContent` が利用可能なモデルを自動検出して再試行する処理を追加。
   - 1度成功したモデル名はプロセス内でキャッシュし、2回目以降の呼び出しでは最初からそのモデルを使用。
   - エラー発生時にレスポンス本文もログへ出力するよう改善。
