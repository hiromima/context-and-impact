# OpenClaw 現状・理想・ギャップ分析

> 調査日: 2026-03-24
> バージョン: OpenClaw 2026.3.13

---

## 現状サマリー

```
MacBook Pro (Worker Node)
├── Node 接続: wss://aai.tailba4b9d.ts.net:443  ← OK
├── ローカルエージェント: 10体（うち設定不全 5体）
├── スキル: 52個（36 ready / 16 missing）
├── Cron: 28ジョブ（3件エラー）
├── フック: 4/4 ready  ← OK
└── 診断: 8件の警告・問題
```

---

## 問題一覧（現状 vs 理想）

### P0: 即時対応必須

| # | 問題 | 現状 | 理想 | 深刻度 |
|---|------|------|------|--------|
| 1 | **設定ファイルが2箇所に分裂** | `~/.openclaw/openclaw.json`（10 agents）と `~/.openclaw/.openclaw/openclaw.json`（5 agents）が共存 | 1ファイルのみ。`~/.openclaw/openclaw.json` が唯一の正 | 🔴 高 |
| 2 | **設定ファイルのパーミッション** | `~/.openclaw/.openclaw/openclaw.json` が `-rw-r--r--`（world readable） | `chmod 600` で所有者のみ読み書き | 🔴 高 |
| 3 | **android-dev のワークスペース消失** | `/Users/shunsukehayashi/dev/ppal-companion` が存在しない | 正しいパスに向けるか削除 | 🔴 高 |

### P1: 早期対応推奨

| # | 問題 | 現状 | 理想 |
|---|------|------|------|
| 4 | **SNS エージェントの共有ワークスペース** | `sns-engagement`, `sns-creator`, `sns-strategist` が `/openclaw-workspace/` ルートを共有 | 各エージェントに個別ディレクトリ |
| 5 | **memory/ ディレクトリが存在しない** | `~/.openclaw/workspace/memory` が missing → main の長期記憶が動かない | `mkdir -p` で作成 |
| 6 | **Cron エラー 3 件** | `Knowledge Watcher`, `daily-summary`, `weekly-project-review` が error 状態 | 原因特定して修正 or 無効化 |
| 7 | **旧 LaunchAgent が残留** | `ai.openclaw.firehose-listener.plist` が active（ステータス `-` = 起動失敗中） | 完全に無効化・削除 |
| 8 | **openai-codex の認証なし** | フォールバックに `openai-codex/gpt-5.2` が設定されているが認証情報なし | 認証を追加するか fallbacks から削除 |

### P2: 改善推奨

| # | 問題 | 現状 | 理想 |
|---|------|------|------|
| 9 | **フォールバックに primary と同じモデル** | fallbacks[0] = `anthropic/claude-sonnet-4-6` (primary と重複) | 冗長エントリを削除 |
| 10 | **旧環境変数 `CLAWDBOT_HOME`** | `.zshrc`/`.zshenv` に残存している可能性 | `OPENCLAW_HOME` に置き換え |
| 11 | **ローカルエージェントに不要な5体** | `sns-engagement/creator/strategist/analytics`（旧定義）、`android-dev`（ws消失）がローカルに残る | Gateway 側で管理し、ローカルは最小構成に |
| 12 | **Discord が未設定だが enabled: true** | channels.discord.enabled = true だが bot token 未設定 | 使わないなら `enabled: false` に変更 |

---

## 詳細な現状スナップショット

### 設定ファイル（2箇所）

```
~/.openclaw/openclaw.json          ← ACTIVE（5548 bytes, 2026-03-19, chmod 600 OK）
  agents.list: 10体
  gateway.remote.url: wss://aai.tailba4b9d.ts.net:443

~/.openclaw/.openclaw/openclaw.json ← 内部（4494 bytes, 2026-03-13, 644 = 問題）
  agents.list: 5体（main, kotowari-dev, guardian, ctx-eng, github-hook）
  gateway.remote.url: wss://aai.tailba4b9d.ts.net:443
```

### エージェント現状（ローカル openclaw.json の 10体）

| ID | モデル | ワークスペース | 状態 |
|----|--------|---------------|------|
| main | inherit | default | ✅ OK |
| kotowari-dev | claude-sonnet-4-6 | ~/dev/03-products/kotowari-desktop | ✅ OK |
| guardian | claude-sonnet-4-6 | ~/openclaw-workspace/guardian | ✅ OK |
| ctx-eng | claude-sonnet-4-6 | ~/openclaw-workspace/ctx-eng | ✅ OK |
| github-hook | claude-sonnet-4-6 | ~/openclaw-workspace/github-hook | ✅ OK |
| sns-engagement | claude-sonnet-4-6 | ~/openclaw-workspace ← **共有root** | ⚠️ ws共有 |
| sns-creator | claude-sonnet-4-6 | ~/openclaw-workspace ← **共有root** | ⚠️ ws共有 |
| sns-analytics | claude-sonnet-4-6 | ~/openclaw-workspace ← **共有root** | ⚠️ ws共有 |
| sns-strategist | claude-sonnet-4-6 | ~/openclaw-workspace ← **共有root** | ⚠️ ws共有 |
| android-dev | claude-sonnet-4-6 | ~/dev/ppal-companion ← **消失** | 🔴 ws missing |

### モデル設定（現状）

```
Primary:   anthropic/claude-sonnet-4-6
Fallbacks: [claude-sonnet-4-6, openai-codex/gpt-5.2, gemini-2.5-flash, gemini-2.5-flash-lite]
                ↑ primaryと重複        ↑ auth設定なし
```

### LaunchAgent（現状）

```
ai.openclaw.node.plist          → アクティブ（起動中）  ← 正常
ai.openclaw.node.plist.disabled → 無効化済み            ← 残留（削除推奨）
ai.openclaw.firehose-listener.plist → アクティブだが失敗 ← 問題あり
ai.hayashi.openclaw-gateway-restart-watch.plist.disabled → 無効化済み OK
ai.hayashi.openclaw-main-empty-payload-watch.plist.disabled → 無効化済み OK
```

### Cron エラー（現状）

```
Knowledge Watcher   → every 6h  → error（2h ago）
daily-summary       → 0:00 JST  → error（11h ago）
weekly-project-review → 月 0:00 → error（1d ago）
```

---

## 理想状態の定義

### エージェント理想構成（MacBook Pro ローカル）

```
agents.list: 5体のみ（必要最小限）
├── main         - 汎用メイン（inherit model）
├── kotowari-dev - KOTOWARI 専属（claude-sonnet-4-6）
├── guardian     - 監視（claude-sonnet-4-6）
├── ctx-eng      - コンテキストエンジニア（claude-sonnet-4-6）
└── github-hook  - GitHub Webhook（claude-haiku-4-5）← haiku で十分
```

※ SNS系エージェントは Windows Gateway 側で定義・管理。ローカル重複不要。

### モデル理想設定

```
Primary:   google/gemini-2.5-flash     ← Anthropic 429 悪循環回避
Fallbacks: [anthropic/claude-sonnet-4-6, google/gemini-2.5-flash-lite]
           ↑ 冗長除去                    ↑ openai-codex 削除
```

### ワークスペース理想構成

```
main         → ~/.openclaw/workspace          （SOUL.md, MEMORY.md等）
kotowari-dev → ~/dev/products/kotowari/       （正規パスに合わせる）
guardian     → ~/openclaw-workspace/guardian  （現状維持）
ctx-eng      → ~/dev/tools/context-and-impact （このプロジェクトと連動）
github-hook  → ~/openclaw-workspace/github-hook（現状維持）
```

### 設定ファイル理想構成

```
~/.openclaw/openclaw.json      ← 唯一の正（chmod 600）
~/.openclaw/.openclaw/         ← 内部生成物のみ（openclaw.json は削除）
```

---

## 修正手順（優先度順）

### Step 1: 設定ファイルのパーミッション修正 [P0 / 5分]

```bash
# .openclaw/.openclaw/openclaw.json のパーミッション修正
chmod 600 ~/.openclaw/.openclaw/openclaw.json

# アクティブな openclaw.json は既に 600 → 確認のみ
ls -la ~/.openclaw/openclaw.json
# -rw------- が正しい
```

### Step 2: android-dev エージェントの修正 [P0 / 5分]

```bash
# ① ppal-companion の正しいパスを探す
find ~/dev -name "ppal-companion" -maxdepth 4 2>/dev/null
ls ~/dev/products/ | grep -i ppal

# ② パスが見つかった場合 → 設定更新
openclaw config set agents.list[9].workspace "/正しいパス"

# ③ パスが見つからない場合 → エージェント削除
openclaw agents delete --agent android-dev
```

### Step 3: SNS エージェントのワークスペース修正 [P1 / 15分]

```bash
# 個別ワークスペースディレクトリを作成
mkdir -p ~/openclaw-workspace/sns-engagement
mkdir -p ~/openclaw-workspace/sns-creator
mkdir -p ~/openclaw-workspace/sns-strategist

# 設定を更新（インデックスは openclaw.json で確認してから）
# sns-engagement = index 5, sns-creator = 6, sns-analytics = 7, sns-strategist = 8
openclaw config set "agents.list[5].workspace" "/Users/shunsukehayashi/openclaw-workspace/sns-engagement"
openclaw config set "agents.list[6].workspace" "/Users/shunsukehayashi/openclaw-workspace/sns-creator"
openclaw config set "agents.list[8].workspace" "/Users/shunsukehayashi/openclaw-workspace/sns-strategist"

# sns-analytics は既に個別ディレクトリあり → index 7 は変更不要

# 変更確認
openclaw config get agents.list
```

### Step 4: memory ディレクトリの作成 [P1 / 2分]

```bash
mkdir -p ~/.openclaw/workspace/memory

# 動作確認
openclaw memory status
# "memory directory missing" が消えるはず
```

### Step 5: firehose-listener LaunchAgent の無効化 [P1 / 5分]

```bash
# まず何をするものか確認
cat ~/Library/LaunchAgents/ai.openclaw.firehose-listener.plist | head -20

# 停止・無効化
launchctl bootout gui/$UID/ai.openclaw.firehose-listener 2>/dev/null
mv ~/Library/LaunchAgents/ai.openclaw.firehose-listener.plist \
   ~/Library/LaunchAgents/ai.openclaw.firehose-listener.plist.disabled

# 古い .plist.disabled も削除
rm -f ~/Library/LaunchAgents/ai.openclaw.node.plist.disabled
```

### Step 6: openai-codex を fallbacks から削除 [P1 / 3分]

```bash
# 現在の fallbacks 確認
openclaw config get agents.defaults.model.fallbacks

# openai-codex を除いた新しいリストに更新
# （primary と同じ claude-sonnet-4-6 の重複も除去）
openclaw models fallbacks list

# フォールバックを ideal に設定
# ※ models fallbacks コマンドでのリスト編集が難しい場合は config set を使う
openclaw config set agents.defaults.model.fallbacks \
  '["anthropic/claude-sonnet-4-6","google/gemini-2.5-flash","google/gemini-2.5-flash-lite"]'
```

### Step 7: Cron エラーの調査・修正 [P1 / 20分]

```bash
# 各エラージョブの最新実行ログを確認
openclaw cron runs b9d932ca-016a-4ea4-be4e-afc4805d2ed9  # Knowledge Watcher
openclaw cron runs cd020642-415e-47af-8125-0ce3bc04f786  # daily-summary
openclaw cron runs 48cc17ca-874d-41f7-aadf-ca9da196e220  # weekly-project-review

# 今すぐ実行してエラー内容確認
openclaw cron run b9d932ca-016a-4ea4-be4e-afc4805d2ed9

# エラーが修正できない場合は一時無効化
openclaw cron disable b9d932ca-016a-4ea4-be4e-afc4805d2ed9
```

### Step 8: 内部 openclaw.json のクリーンアップ [P2 / 5分]

```bash
# アクティブな設定が ~/.openclaw/openclaw.json であることを確認
openclaw config file
# → /Users/shunsukehayashi/.openclaw/openclaw.json が出力されれば OK

# 内部ファイルをバックアップして削除（ただし実績のある設定なので慎重に）
cp ~/.openclaw/.openclaw/openclaw.json ~/.openclaw/.openclaw/openclaw.json.bak.cleanup
# ※ 削除は openclaw が自動再生成するため安全だが、念のためバックアップ後に実施
# rm ~/.openclaw/.openclaw/openclaw.json  ← 慎重に判断
```

### Step 9: モデル primary を gemini に変更 [P2 / 5分]

```bash
# Anthropic 429 悪循環対策（必要に応じて）
openclaw config set agents.defaults.model.primary "google/gemini-2.5-flash"

# github-hook は haiku で十分
openclaw config set "agents.list[4].model" "google/gemini-2.5-flash-lite"

# 変更確認
openclaw models status
```

### Step 10: ctx-eng のワークスペースを最適化 [P2 / 5分]

```bash
# ctx-eng のワークスペースを context-and-impact に向ける
openclaw config set "agents.list[3].workspace" \
  "/Users/shunsukehayashi/dev/tools/context-and-impact"

# context-and-impact の SOUL.md / HEARTBEAT.md を作成（任意）
cat > ~/dev/tools/context-and-impact/HEARTBEAT.md << 'EOF'
# HEARTBEAT — ctx-eng

このエージェントは context-and-impact スキルの専属エージェントです。

## 毎回実行すること
1. L1-L4 コンテキスト収集
2. Agent Skill Bus への実行記録
3. GitNexus インパクト分析

## 主要コマンド
- `python3 src/cli/semantic-search.py --status`
- `npx agent-skill-bus flagged`
EOF
```

---

## 修正後の理想状態チェックリスト

```
□ ~/.openclaw/openclaw.json → chmod 600 OK
□ ~/.openclaw/.openclaw/openclaw.json → chmod 600 OK
□ android-dev → ワークスペース修正 or 削除
□ sns-engagement/creator/strategist → 個別 ws あり
□ ~/.openclaw/workspace/memory → 作成済み
□ ai.openclaw.firehose-listener.plist → 無効化済み
□ openai-codex → fallbacks から削除
□ Cron エラー → 0件
□ openclaw doctor → 警告 0 件（セキュリティ警告は意図的なので除外）
```

---

## 変更前後の比較

| 項目 | Before | After |
|------|--------|-------|
| 設定ファイル | 2箇所に分裂 | 1箇所（active のみ有効） |
| 設定パーミッション | 一部 644 | 全て 600 |
| ローカルエージェント | 10体（5体問題あり） | 5体（全て正常） |
| SNS ワークスペース | 4体が root 共有 | 各自個別 |
| memory/ ディレクトリ | なし（記憶機能不全） | あり（正常動作） |
| Cron エラー | 3件 | 0件 |
| 旧 LaunchAgent | 1件起動失敗中 | 完全クリーンアップ |
| model fallbacks | 重複・認証なしモデル含む | クリーンな 3モデル |
| openclaw doctor 警告 | 8件 | 2件以下（意図的設定除く） |

---

*生成: 2026-03-24 / context-and-impact docs/openclaw-gap-analysis.md*
