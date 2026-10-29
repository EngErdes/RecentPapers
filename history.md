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

---

## 2026-10-26: Gemini API の一時的な高負荷（503 Service Unavailable）時のリトライ・フォールバック対応

### 原因
`gemini-3-flash-preview` へのリクエスト自体は到達していたが、Google 側の一時的なアクセス集中により `503 Service Unavailable`（`This model is currently experiencing high demand. Spikes in demand are usually temporary.`）が返された。

従来の実装では `404` のときのみ別モデルへフォールバックしており、`503`（一時的な高負荷）や `429`（レート制限）では即座に例外終了していた。

### 修正内容
- **`ai.py`（`_complete_json_gemini`）**
  - 一時的エラー（`503` / `429` / `500` / `502` / `504`）が返された場合、即座に次の候補モデル（`gemini-3.1-flash-lite-preview` 等）へ切り替えて試行するよう改善。
  - 全候補が一時的に混雑していた場合も、指数バックオフ（3秒 → 6秒）で待機して最大3ラウンド自動リトライする処理を追加。
  - 一度 `404` を返したモデルは `_unavailable_gemini_models` に記録し、以降の呼び出しやリトライ時にスキップするよう最適化。

---

## 2026-10-26: Gemini 3 Flash 無料枠 1日上限（429 RPD）対策・ローカル HTML パース化

### 原因
1. **途中の `[pdf] 取得失敗 (418 / 403)`**:
   - IEEE Xplore や ScienceDirect 等の出版社サイトによるボット対策・有料壁で PDF 直接取得が拒否されたログ。`PDF が見つからずスキップ` として正常にスキップされ、Notion 登録自体は成功している。
2. **最後の `429 Client Error: Too Many Requests`**:
   - `gemini-3-flash-preview` の無料枠（Free Tier）の1日あたりのリクエスト上限（20回/日: `Generate content requests per day limit exceeded on Free Tier`）に達したことが原因。
   - メール HTML からの論文抽出（1通1回）と各論文の日本語解説生成（1論文1回）で API を消費していたため、メール数が多いと早期に 20回/日の上限に到達していた。

### 修正内容（モデルは `gemini-3-flash-preview` のみを使用）
1. **Google Scholar メール HTML のローカル解析（`ai.py`: `_extract_papers_from_html`）**
   - Google Scholar アラート固有の HTML 構造（`gse_alrt_title`・`color:#006621`・`gse_alrt_sni`）からタイトル・著者・掲載誌・発行年・スニペット・PDF/DOI/Git URL をローカルで直接抽出。
   - これによりメール HTML 抽出での API 呼び出しが **0回** となり、登録済み論文のスキップ判定まで API 枠を一切消費しない（ローカル抽出で 0 件だった場合のみ AI 抽出にフォールバック）。
2. **使用モデルを `gemini-3-flash-preview` に一本化し、リトライと1日上限判定を改善（`ai.py`: `_complete_json_gemini`）**
   - 別モデルへのフォールバックを廃止し、`GEMINI_MODEL`（`"gemini-3-flash-preview"`）のみを使用。
   - 一時的な高負荷（`503`）や分間レート制限（`429 RPM`）に対しては `5秒 → 10秒 → 20秒 → 30秒` のバックオフでリトライ。
   - `_is_daily_quota_exceeded` で1日あたりの無料枠上限（`429 RPD` / `free_tier_requests`）と判定された場合は無駄なリトライを行わず即座に `QuotaExhaustedError` を送出。
3. **クォータ上限到達時の安全な途中終了（`scholar_to_notion.py`）**
   - `QuotaExhaustedError` をキャッチしてそこまでの登録件数を出力し、エラー終了（exit code 1）ではなく正常終了（exit code 0）するよう変更。残りの未登録論文は次回実行時に続きから処理される。

---

## 2026-10-26: Notion 登録済み論文タイトルの重複スキップ判定の強化

### 変更内容
1. **`notion.py`**
   - `fetch_registered_titles`: 従来の「原題」カラムだけでなく、「タイトル」（`title` 型）カラムの文字列も両方取得して重複チェック集合に含めるよう拡張。
   - `normalize_title`: 空白・大文字小文字の正規化に加え、Google Scholar 特有の先頭バッジ（`[PDF]` / `[HTML]` 等）の除去およびダッシュ・ハイフン類（`–`, `—`, `−` 等 → `-`）の統一を行い、表記揺れによる重複登録を防止。
2. **`ai.py`**
   - `_extract_papers_from_html`: HTML から論文タイトルを抽出する際、先頭に `[PDF]` 等のバッジが含まれていれば除去してクリーンな原題として保持するよう改善。
3. **`scholar_to_notion.py`**
   - PDF 取得・AI 呼び出し前に原題で重複チェックを行い、さらに AI が生成した日本語タイトルでも重複チェックを実施。新規登録時には原題・日本語タイトルの両方を登録済み集合に追加して同一実行内の重複も防止。

---

## 2026-10-28: 未登録の論文が 20 件取得できるまで過去のメールを遡る対応＆原題正規化の厳密化

### 変更内容
1. **未登録論文が 20 件に達するまで過去のメールを遡る処理（`config.py` / `gmail.py` / `scholar_to_notion.py`）**
   - `config.py`: `MAX_PAPERS_PER_RUN`（デフォルト: `20`、環境変数で変更可）を追加。あわせて `DEBUG` のデフォルトを `False` に変更。
   - `gmail.py`: 「直近 72 時間」の時間制限で打ち切らず、ラベル内の全メッセージを新しい側から 200 件ずつバッチ取得して過去へ遡るジェネレータ `iter_threads_newest_first` を追加。
   - `scholar_to_notion.py`: 新しいメールから順にローカル HTML パース（API 消費 0）で論文を抽出し、登録済み論文はスキップ（API 消費 0）しながら、未登録論文が `MAX_PAPERS_PER_RUN`（20 件＝Gemini API 20 回分）登録できた時点で処理を完了するよう変更。

2. **原題の重複判定・HTML 抽出の厳密化（`notion.py` / `ai.py`）**
   - `notion.py`（`normalize_title`）: Google Scholar の HTML に含まれるソフトハイフン（`\u00ad`）やゼロ幅文字を除去したうえで、記号・句読点・空白を除いた文字＋数字列で比較するよう強化し、表記揺れによる重複登録や不要な API 消費を防止。
   - `ai.py`（`_strip_tags` / `extract_papers_with_claude`）: テキスト抽出時にソフトハイフン・ゼロ幅文字を除去し、HTML 抽出時の AI フォールバックを廃止して HTML 解析での API 消費を完全に 0 回に固定。

---

## 2026-10-28: 最初の 1 件の要約内容を PDF 化し新しい Git ブランチに `README.pdf` として登録する機能を追加

### 変更内容
1. **日本語要約 PDF 生成（`pdf.py`: `generate_summary_pdf_bytes` / `pyproject.toml`）**
   - `reportlab` の内蔵日本語 CID フォント（`HeiseiKakuGo-W5`）を使用し、Gemini API で生成した日本語タイトル・原題・著者・掲載誌・各種リンク・一言キャッチコピー・要約・問題設定・新規性・大学 1 年生向け解説を A4 PDF として整形・出力する関数を追加。
2. **Git 新規ブランチへの `README.pdf` 登録・push（`git_publish.py`: `publish_readme_pdf_to_branch`）**
   - `paper/YYYYMMDD-論文タイトルスラグ` 形式のブランチを新規作成し、リポジトリ直下に `README.pdf` を配置してコミット＆`origin` へ push したのち、元のブランチ（`main`）へ自動で戻るモジュールを追加。
3. **パイプラインおよび GitHub Actions 権限の連動（`scholar_to_notion.py` / `.github/workflows/main.yml`）**
   - `scholar_to_notion.py`: 最初の 1 件の未登録論文（`total == 1`）を登録したタイミングで要約 PDF を生成し、新規 Git ブランチへ `README.pdf` として登録・push する処理を追加。
   - `.github/workflows/main.yml`: GitHub Actions から新規ブランチを push できるよう `permissions: contents: write` を追加。

---

## 2026-10-28: 新規 Git ブランチに `README.pdf` とあわせて `README.md` も同時出力・登録する対応

### 変更内容
1. **`git_publish.py`**
   - `generate_summary_markdown`: 日本語タイトル・原題・著者・掲載誌・各種 URL・`[README.pdf](./README.pdf)` へのリンク・一言キャッチコピー・要約・問題設定・新規性・大学 1 年生向け解説を GitHub 表示用の Markdown 形式に整形する関数を追加。
   - `publish_readme_pdf_to_branch`: 新しいブランチ（`paper/YYYYMMDD-論文タイトルスラグ`）のリポジトリ直下に `README.pdf` と `README.md` の両方を出力してコミット＆`origin` へ push し、元のブランチ（`main`）に戻るように拡張。
2. **`scholar_to_notion.py`**
   - 最初の 1 件（`total == 1`）の処理時に `generate_summary_markdown` も呼び出し、`README.pdf` と `README.md` をセットで新ブランチに登録するよう更新。これにより GitHub 上で該当ブランチを開いた際、ページ下部に要約が自動展開されてすぐ閲覧できるようになった。

---

## 2026-10-28: 論文の新規性にフォーカスした図解（フローチャート）を `README.pdf`・`README.md` に追加

### 変更内容
1. **新規性に特化した図解ステップ生成（`ai.py`: `generate_japanese_content`）**
   - 既存の日本語コンテンツ生成プロンプト（1 回の API 呼び出し）の返却 JSON に、新規性にフォーカスした 4 ステップの `diagram_steps` を追加（追加の API 呼び出し枠は消費しない）。
     1. `1. 先行研究の限界`: 従来手法のボトルネック・未解決課題
     2. `2. 本研究の着眼点`: 従来とは異なる新しい発想・アプローチ
     3. `3. 技術的な新規性`: それを実現する具体的な仕組み・構造・アルゴリズムの工夫
     4. `4. 新規性による優位性`: この新規性によって初めて達成できた性能・ブレークスルー
2. **`README.pdf` への図解描画（`pdf.py`: `extract_diagram_steps` / `_build_diagram_flowables`）**
   - 「■ 新規性の図解（先行研究との違いと本研究のブレークスルー）」セクションを追加し、色分けされたステップカードと矢印（`▼`）によるフローチャート図を PDF 内に描画。
3. **`README.md` への Mermaid 図解追加（`git_publish.py`: `_build_mermaid_diagram`）**
   - 「📊 新規性の図解（先行研究との違いと本研究のブレークスルー）」セクションを追加し、GitHub 上で自動レンダリングされる色付きの Mermaid フローチャート（`flowchart TD`）を出力。

---

## 2026-10-29: Notion への論文追加時に実行日（日付カラム）を自動記録する対応

### 変更内容
- **`notion.py`**
  - `_ALIAS_DATE`（`"日付"`, `"登録日"`, `"追加日"`, `"取得日"`, `"Date"`, `"date"`）を追加。
  - `create_notion_page` でパイプライン実行時の日本時間（JST）の日付 `YYYY-MM-DD` を取得し、日付カラム（エイリアス名一致、または DB スキーマ内の `date` 型カラム）へ自動セットするよう更新（GitHub Actions の UTC 環境でも日本時間の日付が記録される）。

---

## 2026-10-29: `main` ブランチに `README.md` を追加し、要約論文ブランチへのリンクを日付降順の表形式で自動追記する対応

### 変更内容
1. **`README.md`（新規作成）**
   - プロジェクトの概要・機能・実行方法・環境変数・モジュール構成をまとめた `README.md` を `main` ブランチに追加し、上部に「📚 要約済み論文一覧」テーブル（`| 日付 | 論文タイトル |`）を配置。
2. **`git_publish.py`（`_insert_row_into_readme` / `_update_main_readme_index`）**
   - 新規ブランチ（`paper/YYYYMMDD-slug`）への `README.pdf`・`README.md` の push 成功後、`main` ブランチに戻ったうえで `main` ブランチの `README.md` のテーブルに `| YYYY-MM-DD | [日本語タイトル](対応ブランチURL) |` を追記してコミット＆push する処理を追加。
   - テーブル内の行は常に日付の降順（新しい日付ほど上、同日なら最新追加分が最上部）に整列される。
3. **`scholar_to_notion.py`**
   - `publish_readme_pdf_to_branch` 呼び出し時に日本語タイトル（`japanese_title`）を渡すように更新。

---

## 2026-10-29: `README.pdf`・`README.md` に記載される各種 URL をクリック可能なリンクとして出力する対応

### 変更内容
1. **`pdf.py`（`generate_summary_pdf_bytes`）**
   - PDF・DOI・Git リポジトリ・原文リンク等の URL（`http://` / `https://`）を ReportLab のハイパーリンクタグ（`<a href="..." color="#1a0dab"><u>URL</u></a>`）で出力し、PDF ビューア上でクリックして開けるよう更新。
2. **`git_publish.py`（`generate_summary_markdown`）**
   - `http://` / `https://` で始まる項目を明示的な Markdown リンク形式（`[URL](URL)`）で出力するよう更新。

---

## 2026-10-29: `README.pdf`・`README.md` の新規性図解を横長ボックスに刷新し、全体のマージン・レイアウトを美化する対応

### 変更内容
1. **PDF の横長カード図解と全体レイアウト改善（`pdf.py`: `_build_diagram_flowables`, `generate_summary_pdf_bytes`）**
   - ページ余白を上下左右各 `20 mm`（本文幅 `170 mm`）に設定。
   - 新規性図解の各ステップを、左右にさらに各 `15 mm` の余白を設けた中央揃えの横長2カラム角丸カード（幅 `140 mm` ＝ 左ステップバッジ列 `34 mm` ＋ 右テキスト列 `106 mm`）に刷新し、上下余白と矢印（`▼`）の間隔もバランスよく調整。
   - タイトル直下に「💡 一言要約」のハイライトバナー、および2カラムのメタデータ表（クリック可能なリンク付き）を配置。
2. **Markdown の横長 Mermaid 図解と全体レイアウト改善（`git_publish.py`: `_build_mermaid_diagram`, `generate_summary_markdown`）**
   - Mermaid の `flowchart` 設定（`wrappingWidth: 520`, `padding: 14`, `rankSpacing: 28`）と区切り線・`<br/>` 改行・角丸スタイル（`rx:8,ry:8`）により、左右に適切な余白を残した美しい縦横比の横長ボックスに改善。
   - 冒頭に `> **💡 一言要約**` のコールアウトと2カラムのメタデータ表を配置し、全体の可読性を向上。

---

## 2026-10-29: Notion に登録されたすべての論文を Git ブランチへ登録する対応

### 変更内容
1. **`scholar_to_notion.py`（`main`）**
   - `if total == 1:` の制限を撤廃し、Notion に新規登録されたすべての論文について `README.pdf`・`README.md` を生成して `paper/YYYYMMDD-slug` ブランチへ push し、`main` ブランチの `README.md` 論文一覧テーブルにも全件追記するように変更。
2. **`git_publish.py`（`publish_readme_pdf_to_branch`）**
   - 連続実行時に元のブランチへ戻る際、万一未追跡の `README.pdf` が残っていた場合でも確実に削除するクリーンアップ処理を追加。
3. **`how_to_use.md`**
   - 機能説明を「最初の1件」から「Notion に登録した全論文」へ更新。
