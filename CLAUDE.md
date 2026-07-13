# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

macOS launchd によって毎日 08:00 に実行される Python パイプライン。処理の流れ:
1. Gmail API（OAuth2）で特定ラベルの Google Scholar アラートメールを取得
2. Claude でメール HTML を解析し、論文メタデータ（タイトル・著者・掲載誌・URL）を抽出
3. Claude で各論文の日本語タイトル・要約・一言キャッチコピー・問題説明・初学者向け解説を生成
4. Notion データベースに論文ごとのレコードを作成

# TODO
github actionsから実行できるように
git hubにもマークダウンを登録

## パイプラインの実行

```bash
# 手動実行（uv が依存関係を自動解決）
uv run python scholar_to_notion.py
```

## 依存関係

`uv` で管理（pyproject.toml + uv.lock）。Python 3.10 以上が必要（`.python-version` 参照）。

```bash
uv sync   # インストール・更新
```

## 必要な認証情報

- `.env`（`.env.example` をコピーして作成）: `ANTHROPIC_API_KEY`、`NOTION_TOKEN`
- `gmail_credentials.json` — Google Cloud Console からダウンロードした OAuth2 クライアントシークレット（gitignore 済み）
- `gmail_token.pickle` — 初回実行時にブラウザ認証フローで自動生成、以降は自動更新

## 主要定数（`config.py`）

| 定数 | 値・取得元 |
|---|---|
| `GMAIL_LABEL` | `"01.日々の情報収集/01.03GoogleScholar"` |
| `NOTION_DATABASE_ID` | 環境変数、またはハードコードされたデフォルト値 |
| `CLAUDE_MODEL` | `claude-sonnet-4-6` |
| `TOKEN_PATH` | `gmail_token.pickle`（スクリプトと同ディレクトリ）|
| `CREDENTIALS_PATH` | `gmail_credentials.json`（スクリプトと同ディレクトリ）|

## launchd スケジューリング（macOS）

`com.erdes.scholar_to_notion.plist` で毎日定時実行を設定。

```bash
# 有効化
launchctl load ~/Library/LaunchAgents/com.erdes.scholar_to_notion.plist

# 無効化
launchctl unload ~/Library/LaunchAgents/com.erdes.scholar_to_notion.plist

# 即時実行
launchctl start com.erdes.scholar_to_notion
```

ログはプロジェクトルートの `scholar_to_notion.log`（標準出力）と `scholar_to_notion_error.log`（標準エラー）に出力される。

## コード生成の方針

コードを生成・追加する際は、適切にモジュール分割して生成すること。

## モジュール構成

| ファイル | 役割 |
|---|---|
| `scholar_to_notion.py` | エントリポイント。パイプライン全体を統括 |
| `config.py` | 定数と環境変数のロード |
| `gmail.py` | Gmail OAuth2 認証・スレッド取得・本文パース |
| `ai.py` | Claude API 呼び出し2種（論文抽出・日本語コンテンツ生成）|
| `notion.py` | Notion ページ・ブロック生成ヘルパー |

論文1件あたりの処理: `ai.extract_papers_with_claude` で HTML を解析 → `ai.generate_japanese_content` で日本語コンテンツを生成 → `notion.create_notion_page` でレコードを書き込む。Claude の両呼び出しは共通の `_parse_json` ヘルパーを使用しており、レスポンスに誤って含まれるマークダウンフェンスを除去し、JSON が不正な場合は正規表現でフォールバック抽出する。

Notion ページの構成: データベースプロパティ（タイトル・著者・掲載誌・要約・キーワード・PDF/DOI URL）＋オプションのブロック本文（一言要約・問題説明・初学者向け解説・原文リンク）。
