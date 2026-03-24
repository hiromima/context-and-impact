# OpenClaw Engineering ガイド

> 調査日: 2026-03-24
> バージョン: OpenClaw 2026.3.13 (61d171a)
> 対象環境: MacBook Pro（Worker Node）+ Windows Gateway (AAI)

---

## 1. アーキテクチャ概要

OpenClaw は **Gateway + Worker Node** の分散クラスター構成。

```
┌─────────────────────────────────────────────────────────────────┐
│  Windows Gateway (aai.tailba4b9d.ts.net)                        │
│  ws://127.0.0.1:18789 (local) / wss://aai...:443 (Tailscale)   │
│  エージェント定義・Cron・チャンネル・スキルを一元管理            │
├────────────────┬─────────────────┬───────────────┬─────────────┤
│ Worker-MainMini│ Worker-MacMini2 │ Worker-Mini3  │MacBook Pro  │
│ (mainmini)     │ (macmini2)      │ (mini3)       │(local)      │
└────────────────┴─────────────────┴───────────────┴─────────────┘
```

### MacBook Pro ノード設定 (`~/.openclaw/node.json`)

```json
{
  "nodeId": "378f2a9f-00f9-43d3-af08-ac026f37eaa8",
  "displayName": "ShunsukeのMacBook Pro",
  "gateway": {
    "host": "aai.tailba4b9d.ts.net",
    "port": 443,
    "tls": true
  }
}
```

---

## 2. 設定システム

### 設定ファイルの場所

| 環境         | パス                                                       |
|--------------|------------------------------------------------------------|
| MacBook Pro  | `~/.openclaw/openclaw.json`                                |
| Windows Gateway | `C:\Users\shuns\Dev\openclaw-state-2\openclaw.json`    |
| ノード接続先 | `~/.openclaw/node.json` ← **これが実際の接続先を決定**     |

### config コマンド（非破壊的な設定変更の正規手段）

```bash
# 値の取得
openclaw config get agents.defaults
openclaw config get gateway
openclaw config get channels

# 値の設定
openclaw config set agents.defaults.model.primary "anthropic/claude-sonnet-4-6"
openclaw config set agents.list[0].tools.exec.host "gateway"

# 値の削除
openclaw config unset agents.list[0].tools.exec.node

# 設定ファイルのパス確認
openclaw config file

# 設定の妥当性チェック（起動なし）
openclaw config validate
```

### 主要な設定パス（dot-path）

| パス | 説明 |
|------|------|
| `gateway.mode` | `local` or `remote` |
| `gateway.bind` | `loopback` (127.0.0.1) or `all` |
| `gateway.remote.url` | リモート Gateway の WebSocket URL |
| `gateway.auth.token` | Gateway 認証トークン |
| `agents.defaults.model.primary` | 全エージェントのデフォルトモデル |
| `agents.defaults.model.fallbacks` | フォールバックモデルリスト |
| `agents.defaults.workspace` | デフォルトワークスペースパス |
| `agents.defaults.maxConcurrent` | 最大並行エージェント数 |
| `agents.defaults.subagents.maxConcurrent` | サブエージェント最大並行数 |
| `agents.list[N].id` | エージェント ID |
| `agents.list[N].model.primary` | 個別モデル指定 |
| `agents.list[N].tools.exec.host` | exec 実行先 (`gateway` or ノード名) |
| `agents.list[N].tools.exec.node` | exec 実行ノード（**main には設定しない**） |
| `agents.list[N].workspace` | エージェント作業ディレクトリ |
| `agents.list[N].heartbeat.intervalSeconds` | Heartbeat 間隔 |
| `channels.telegram.enabled` | Telegram 有効化 |
| `channels.telegram.allowFrom` | 許可 Telegram ユーザー ID リスト |
| `channels.telegram.dmPolicy` | `allowlist` or `open` |

---

## 3. エージェント管理

### MacBook Pro のローカルエージェント（5体）

| ID | モデル | workspace | 用途 |
|----|--------|-----------|------|
| `main` | inherit (defaults) | default | 汎用メインエージェント |
| `kotowari-dev` | claude-sonnet-4-6 | `~/dev/03-products/kotowari-desktop` | KOTOWARI 専属開発 |
| `guardian` | claude-sonnet-4-6 | `~/openclaw-workspace/guardian` | Guardian 監視 |
| `ctx-eng` | claude-sonnet-4-6 | `~/openclaw-workspace/ctx-eng` | コンテキストエンジニア |
| `github-hook` | claude-sonnet-4-6 | `~/openclaw-workspace/github-hook` | GitHub Webhook 処理 |

### デフォルトモデル設定（MacBook Pro）

```
Primary: anthropic/claude-sonnet-4-6
Fallbacks:
  1. anthropic/claude-sonnet-4-6
  2. openai-codex/gpt-5.2
  3. google/gemini-2.5-flash
  4. google/gemini-2.5-flash-lite
```

### エージェント追加・管理コマンド

```bash
# エージェント追加
openclaw agents add

# エージェント一覧
openclaw agents list

# ルーティングバインド追加（チャンネル → エージェント）
openclaw agents bind --agent kotowari-dev --channel telegram --target @user

# バインド一覧
openclaw agents bindings

# エージェント削除
openclaw agents delete --agent <id>

# エージェントIDを指定してターンを実行
openclaw agent --to @user --message "テスト" --deliver
```

---

## 4. モデル管理

### モデルコマンド

```bash
# 設定済みモデル一覧
openclaw models list

# モデル状態確認
openclaw models status

# デフォルトモデル変更
openclaw models set anthropic/claude-opus-4-6

# イメージモデル変更
openclaw models set-image google/gemini-2.0-flash

# フォールバックリスト管理
openclaw models fallbacks list
openclaw models fallbacks add google/gemini-2.5-flash
openclaw models fallbacks remove <model>

# エイリアス管理
openclaw models aliases set sonnet anthropic/claude-sonnet-4-6

# OpenRouter フリーモデルのスキャン
openclaw models scan
```

---

## 5. スキルシステム

### スキル構成（MacBook Pro: 52スキル、36 ready）

スキルは `~/.openclaw/skills/<skill-name>/SKILL.md` に配置。

```
~/.openclaw/skills/
├── context-and-impact/       ← このプロジェクトと連動
├── coding-agent/
├── gitnexus/
├── gmail-assistant/
├── openclaw-agent-sync/
├── ...（計49ディレクトリ）
```

#### スキルの種別

| 種別 | 説明 |
|------|------|
| `openclaw-bundled` | OpenClaw 公式バンドルスキル |
| `clawhub` | ClawHub マーケットプレイスから取得 |
| `custom` | ユーザー独自スキル |

### スキル管理コマンド

```bash
# スキル一覧（状態付き）
openclaw skills list

# Ready/Missing チェック
openclaw skills check

# スキル詳細
openclaw skills info context-and-impact

# ClawHub からインストール
openclaw plugins install <skill-name>

# スキルのアップデート
openclaw hooks update
```

### SKILL.md の構造（スキル定義ファイル）

```markdown
---
name: skill-name
version: 1.0.0
runtime: openclaw        # または claude-code
description: |
  スキルの説明
triggers:
  - キーワード1
  - キーワード2
---

# スキル本文

エージェントへの指示・使い方・コマンド例など
```

---

## 6. Cron スケジューラー

### 現在のCronジョブ（28件）

| 名前 | スケジュール | エージェント | モデル | 状態 |
|------|-------------|-------------|--------|------|
| health-check | 6時間毎 | main | claude-4.5-haiku | ok |
| content-draft | 1日毎 | writer | - | ok |
| research-digest | 1日毎 | scholar | - | ok |
| oura-afternoon | 14:00 JST | main | claude-4.5-haiku | ok |
| teaching-review | 1日毎 | sensei | - | ok |
| Knowledge Watcher | 6時間毎 | main | gemini-flash | error |
| gitnexus-reindex | 3:00 JST | main | gemini-flash | ok |
| memory-maintenance | 3:30 JST | main | claude-4.5-haiku | ok |
| daily-summary | 0:00 JST | main | claude-sonnet-4-6 | error |
| ... | ... | ... | ... | ... |

### Cron 管理コマンド

```bash
# 一覧
openclaw cron list

# 追加
openclaw cron add \
  --name "my-job" \
  --schedule "every 6h" \
  --agent main \
  --message "定期タスク内容"

# cron 式（タイムゾーン指定可）
openclaw cron add \
  --name "morning" \
  --schedule "cron 0 9 * * * @ Asia/Tokyo" \
  --agent main \
  --message "朝のタスク"

# 今すぐ実行（デバッグ）
openclaw cron run <job-id>

# 有効化/無効化
openclaw cron enable <job-id>
openclaw cron disable <job-id>

# 編集
openclaw cron edit <job-id> --schedule "every 12h"

# 削除
openclaw cron rm <job-id>

# 実行履歴
openclaw cron runs <job-id>

# スケジューラー状態
openclaw cron status
```

### schedule 書式

```
every 5m          # 5分毎
every 1h          # 1時間毎
every 6h          # 6時間毎
every 1d          # 1日毎
cron 0 9 * * *    # 標準 cron 式（UTC）
cron 0 9 * * * @ Asia/Tokyo    # タイムゾーン付き
cron 0 9 * * 1-5 @ Asia/Tokyo  # 平日のみ
```

---

## 7. チャンネル（Messaging）

### 現在の設定

```
Telegram: 有効
  dmPolicy: allowlist
  allowFrom: [7654362070]  # Android
  streaming: off

Discord: 有効
  groupPolicy: allowlist
  streaming: off
```

### チャンネル管理コマンド

```bash
# チャンネル一覧
openclaw channels list

# 状態確認
openclaw channels status
openclaw channels status --probe  # プローブ実行

# Telegram ボット追加
openclaw channels add --channel telegram --token <bot-token>

# ログ確認
openclaw channels logs --channel telegram

# 機能一覧
openclaw channels capabilities --channel telegram

# ユーザー/グループ ID 検索
openclaw directory --channel telegram @username
```

---

## 8. メモリシステム

### 構成

| 項目 | 値 |
|------|----|
| プロバイダー | gemini |
| モデル | gemini-embedding-001 |
| ストレージ | SQLite + ベクトル検索 |
| FTS | ready |
| ベクトルライブラリ | sqlite-vec-darwin-arm64 |

### メモリ管理コマンド

```bash
# 状態確認
openclaw memory status
openclaw memory status --deep  # プロバイダー readiness も確認
openclaw memory status --json  # JSON 出力

# 再インデックス
openclaw memory index --force
openclaw memory index --force --agent main  # 特定エージェントのみ

# 検索
openclaw memory search "keyword"
openclaw memory search --query "deployment" --max-results 20
```

### ワークスペース内のメモリファイル

```
~/.openclaw/workspace/
├── SOUL.md          # エージェントのアイデンティティ定義
├── USER.md          # ユーザー情報（林駿甫のプロファイル）
├── TOOLS.md         # ローカル環境固有の設定メモ
├── AGENTS.md        # ワークスペースの使い方ルール
├── MEMORY.md        # 長期記憶（main セッションのみロード）
├── HEARTBEAT.md     # Heartbeat 指示書
├── BOOTSTRAP.md     # 初回起動時のみ読む
├── IDENTITY.md      # エージェント自己認識
├── docs/            # 追加ドキュメント
└── memory/          # 日次ログ (YYYY-MM-DD.md)
```

---

## 9. Hooks（フック）

### 現在のフック（4/4 ready）

| フック | 説明 |
|--------|------|
| `boot-md` | Gateway 起動時に BOOT.md を実行 |
| `bootstrap-extra-files` | glob/path パターンで追加ファイルをインジェクト |
| `command-logger` | 全コマンドイベントを監査ログに記録 |
| `session-memory` | `/new` or `/reset` 時にセッションコンテキストをメモリ保存 |

### Hooks 管理コマンド

```bash
# フック一覧
openclaw hooks list

# フック詳細
openclaw hooks info boot-md

# フック有効化/無効化
openclaw hooks enable session-memory
openclaw hooks disable command-logger

# フックパックのインストール
openclaw hooks install /path/to/hook-pack
openclaw hooks install @scope/hook-pack  # npm

# フック更新
openclaw hooks update
```

---

## 10. Node（分散ノード）管理

### ノード管理コマンド

```bash
# ノード一覧（状態付き）
openclaw nodes status

# ノード詳細（対応コマンド一覧）
openclaw nodes describe --node Worker-MainMini --json

# ノードでコマンド実行
openclaw nodes run --node Worker-MainMini --raw "uname -a"

# ノード経由でコマンド実行（headless 対応）
openclaw nodes invoke \
  --node Worker-MainMini \
  --command system.run \
  --params '{"command":["hostname"],"shell":true}'

# ノードのペアリング承認
openclaw nodes pending
openclaw nodes approve <requestId>

# ノード名変更
openclaw nodes rename --node <nodeId> --name "新しい名前"

# スクリーンショット取得
openclaw nodes screen --node <nodeId>

# カメラスナップショット
openclaw nodes camera snap --node <nodeId>

# ローカル通知送信（mac only）
openclaw nodes notify --node <nodeId> --title "テスト" --body "通知本文"
```

### MacBook Pro をノードとして設定

```bash
# ノードサービスのインストール（LaunchAgent 生成）
openclaw node install

# ノードサービスの起動
openclaw node run --host aai.tailba4b9d.ts.net --port 443 --tls

# exec 承認設定
cat > ~/.openclaw/exec-approvals.json << 'EOF'
{
  "version": 1,
  "defaults": { "security": "full", "ask": "off" },
  "agents": {},
  "rules": [{"pattern": "*", "action": "allow"}]
}
EOF
```

---

## 11. ACP（Agent Control Protocol）

ACP は Claude Code / Codex などの外部エージェントから Gateway を経由してエージェントを操作するブリッジ。

```bash
# ACP クライアント起動
openclaw acp client

# セッション指定
openclaw acp --session agent:main:main --url wss://aai.tailba4b9d.ts.net:443

# 既存セッションを継続
openclaw acp --session agent:kotowari-dev:dev --require-existing
```

### ACP セッションキーの形式

```
agent:<agent-id>:<session-name>
例: agent:main:main
    agent:kotowari-dev:dev
```

---

## 12. Gateway 操作

```bash
# Gateway 起動（ローカル）
openclaw gateway

# バックグラウンド起動
openclaw gateway start

# 停止
openclaw gateway stop

# 再起動
openclaw gateway restart

# 状態確認
openclaw health

# ヘルスチェック（詳細）
openclaw doctor
openclaw doctor --deep

# ログ
openclaw logs
openclaw logs --tail 100

# コントロール UI を開く
openclaw dashboard

# TUI を起動
openclaw tui

# リモート Gateway の TUI
openclaw tui --url wss://aai.tailba4b9d.ts.net:443
```

---

## 13. セキュリティ・デバイス管理

```bash
# デバイス一覧
openclaw devices list

# デバイス承認
openclaw devices approve <requestId>

# exec 承認ルール管理
openclaw approvals list
openclaw approvals add --pattern "*" --action allow

# セキュリティ監査
openclaw security

# QRコード生成（iOS ペアリング）
openclaw qr

# バックアップ
openclaw backup create
openclaw backup verify
```

---

## 14. 診断・トラブルシューティング

### よく使う診断コマンド

```bash
# 全体ヘルスチェック
openclaw doctor
openclaw doctor --deep    # プロバイダープローブ含む

# ステータス確認
openclaw status           # チャンネル + セッション
openclaw health           # Gateway ping

# チャンネルログ確認
openclaw channels logs --channel telegram

# Gateway ログ
openclaw logs

# メモリ問題
openclaw memory status --deep
openclaw memory index --force

# モデル認証状態
openclaw models auth list
openclaw models status
```

### 既知の注意事項

| 問題 | 解決策 |
|------|--------|
| `openclaw doctor --fix` は**絶対に実行しない（P0）** | agents.list / channels を全消去する破壊的コマンド |
| Gateway を強制終了しない | `Stop-Process -Name node -Force` は openclaw.json を破壊する |
| `exec.node` を main エージェントに設定しない | Gateway ローカル実行が壊れる |
| MacBook Pro の二重設定ファイル | `~/.openclaw/openclaw.json` と `~/.openclaw/.openclaw/openclaw.json` の両方を確認 |
| mini3 で `bash -l` は nvm を読まない | `export NVM_DIR="$HOME/.nvm" && . "$NVM_DIR/nvm.sh"` を明示 |

---

## 15. context-and-impact との連携

OpenClaw エージェントが context-and-impact スキルを使う際の設定。

### スキルの配置

```
~/.openclaw/skills/context-and-impact/SKILL.md
  └── ~/dev/tools/context-and-impact/skills/openclaw/SKILL.md からシンボリックリンク or コピー
```

### 推奨ワークフロー（OpenClaw エージェント側）

```
@main context --query "JWT 認証 設計"
→ L1: grep -r "JWT" ~/dev/ --include="*.ts" -l | head -20
→ L2a: gitnexus impact authMiddleware --repo kotowari
→ L2b: gitnexus cypher --repo obsidian "MATCH (f:File) WHERE ..."
→ L3: python3 ~/dev/tools/context-and-impact/src/cli/semantic-search.py --query "JWT 認証" --limit 10
```

### Agent Skill Bus 連携

```bash
# スキル実行後の記録
npx agent-skill-bus record-run \
  --skill context-and-impact \
  --result success \
  --metrics '{"quality_score": 4, "layers_used": ["L1","L2a","L3"]}'

# 改善フラグ確認
npx agent-skill-bus flagged
```

---

## 16. 設定変更のベストプラクティス

### DO

```bash
# 設定変更は必ず config コマンドで
openclaw config set <dot.path> <value>

# 変更後は Gateway 再起動
openclaw gateway restart

# 変更前にバックアップ
cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.bak.$(date +%Y%m%d%H%M%S)

# 設定の妥当性確認
openclaw config validate
```

### DON'T

```bash
# openclaw.json を直接編集しない（破損リスク）
# PowerShell の Set-Content は使わない（BOM問題）
# Stop-Process -Name node -Force は使わない（設定破損）
# openclaw doctor --fix は絶対に実行しない（P0）
```

---

*最終更新: 2026-03-24 — context-and-impact docs/openclaw-engineering-guide.md*
