# スキル全体タクソノミー — 完全棚卸し

> 生成日: 2026-03-24
> 総スキル数: 120
> 対象: `~/.claude/skills/` 配下の全スキル

---

## 概要: スキルの全体像

```
~/.claude/skills/                          ← 120 スキル
│
├── [A] Miyabi CLI 基盤          ─── 18 スキル  miyabi-* プレフィックス
├── [B] コードインテリジェンス    ─── 11 スキル  gitnexus-* / gni-* / obsidian-gni
├── [C] エージェントオーケストレーション  ─── 12 スキル  文脈推論・マルチAI統合
├── [D] OpenClaw クラスター       ─── 10 スキル  openclaw-* + pen1-report
├── [E] ナレッジ / Obsidian       ─── 5 スキル   知識管理
├── [F] コンテンツ / SNS          ─── 9 スキル   X・YouTube・note
├── [G] 音声 / TTS                ─── 8 スキル   VOICEVOX・Google Home
├── [H] GitHub / 開発フロー       ─── 7 スキル   Issue駆動・CI/CD
├── [I] Google Workspace          ─── 5 スキル   Gmail・Drive・GAS
├── [J] 通知 / メッセージング     ─── 5 スキル   Telegram・Discord・Pushcut
├── [K] 開発環境 / インフラ       ─── 6 スキル   ターミナル・SSH・Windows
├── [L] パーソナル / アシスタント ─── 5 スキル   林CLI・タスク管理
├── [M] ビジネス / 法務           ─── 4 スキル   法務・税務・資産化
├── [N] 教育 / コース             ─── 2 スキル   PPAL・Udemy
├── [O] クリエイティブ / AI生成   ─── 3 スキル   画像・ゲーム
├── [P] システム管理              ─── 2 スキル   ストレージ
└── [Q] 外部ツール連携            ─── 2 スキル   Craft・Lark
```

---

## [A] Miyabi CLI 基盤 — 18スキル

Miyabi CLIエコシステムの中核。すべての開発オペレーションの起点。

```
miyabi-*
├── A1 コア基盤
│   ├── miyabi-master       マスタープラン仕様書（唯一の真実のソース）★最重要
│   ├── miyabi-onboard      初回オンボーディングウィザード
│   ├── miyabi-setup        環境構築・トークン設定
│   └── miyabi-auth         GitHub認証管理（login/logout/token）
│
├── A2 開発ショートカット
│   ├── miyabi-init         新規リポジトリ作成（53ラベル・26 Actions・Projects V2）
│   ├── miyabi-install      既存プロジェクトへの Miyabi 導入
│   ├── miyabi-build        Issue番号→新機能自動実装
│   ├── miyabi-fix          Issue番号→バグ修正自動実行
│   ├── miyabi-ship         本番デプロイ実行
│   └── miyabi-release      リリース管理（タグ→CI→npm→GitHub Release→X投稿）
│
├── A3 運用・診断
│   ├── miyabi-status       システム全体ステータス確認
│   ├── miyabi-doctor       git/node/npm/GitHub ヘルスチェック
│   ├── miyabi-config       設定値の取得・設定・一覧
│   ├── miyabi-dashboard    プロジェクト状態可視化・TUI
│   └── miyabi-cli-ops      CLI全般運用リファレンス
│
├── A4 実行エンジン
│   ├── miyabi-run          統一実行コマンド（タスク種別→エージェント起動）
│   ├── miyabi-agent        エージェント直接実行（coordinator/codegen/review等）
│   └── miyabi-auto         全自動モード「Water Spider」（自律タスク検知・実行）
│
├── A5 高次パイプライン
│   └── miyabi-omega        6段階完全自動化（分析→計画→実行→テスト→デプロイ→報告）
│
└── A6 スキル・ワークスペース管理
    ├── miyabi-skills-mgmt  スキル一覧・ヘルスチェック・同期
    ├── miyabi-todos        TODOコメント自動検出・GitHub Issue化
    └── miyabi-integration-hub  18スキル統合ワークスペース（最広義の統合点）
```

**context-and-impact との関係**: `miyabi-omega` は context-and-impact の Phase A-E と直接対応する 6 段階パイプライン。`miyabi-auto` は Phase D（Multi-Agent Execution）の自律ループを担う。

---

## [B] コードインテリジェンス — 11スキル

GitNexus を中心としたコードグラフ・影響分析・知識グラフ系。

```
gitnexus-* / gni-* / obsidian-gni
│
├── B1 探索・理解
│   ├── gitnexus-exploring      コード構造の理解・アーキテクチャ探索
│   └── gitnexus-guide          GitNexus ツール・スキーマリファレンス
│
├── B2 影響分析（★ context-and-impact L2a の核心）
│   ├── gitnexus-impact-analysis  blast radius 分析（変更前の安全確認）
│   ├── gni-ops                  GNI 実行・インデックス管理・ナレッジグラフクエリ
│   └── gni-first-agent-orchestration  Impact First 正規オペレーション（DAG生成まで）
│
├── B3 デバッグ
│   └── gitnexus-debugging      バグ追跡・エラー根本原因特定
│
├── B4 リファクタリング
│   └── gitnexus-refactoring    安全なリネーム・抽出・移動
│
├── B5 CLI操作
│   └── gitnexus-cli            analyze/index/status/wiki CLI コマンド
│
├── B6 Obsidian グラフ連携（★ context-and-impact L2b の核心）
│   ├── obsidian-gni            Obsidian wikilink グラフ検索・クロスドメイン探索
│   └── gitnexus-openclaw       GitNexus × OpenClaw 統合
│
└── B7 特殊開発
    └── gitnexus-t025-dev       T025 カーソル可視化機能開発コンテキスト
```

**context-and-impact との関係**: B2 全体が context-and-impact の PHASE C（GNI-First DAG）の実行基盤。L2a = `gitnexus-impact-analysis` + `gni-ops`、L2b = `obsidian-gni`。

---

## [C] エージェントオーケストレーション — 12スキル

マルチAI・自律ループ・パイプライン統合の中枢。

```
│
├── C1 コンテキスト統合パイプライン（★ context-and-impact 本体）
│   └── context-and-impact      5層Context→5フェーズ実行パイプライン（ハブ）
│
├── C2 エージェント実行
│   ├── agent-teams             Claude Code Agent Teams 並列実行
│   ├── multi-agent-orchestration  Codex・OpenClaw・サブエージェント統合管理
│   ├── codex-workers           Codex ワーカー定義・運用手順
│   └── ai-triad                Claude Code / Codex / Gemini 最適役割分担
│
├── C3 DAG・タスク計画
│   └── task-dag-planner        tasks.json depends_on → カニバらない実行順序
│
├── C4 自律フィードバックループ
│   ├── cycle-ops               フィードバックサイクル実行（full/auto/check/health）
│   ├── aria-ldd-add            ARIA v2 LDD+ADD（ログ駆動+監査駆動開発）
│   └── self-improving-skills   スキル自己改善ループ（OBSERVE→APPLY→RECORD）
│
└── C5 ミッション可視化
    ├── miso                    MISO ミッションボード（Telegram/OpenClaw統合）
    ├── miso-spawn              sessions_spawn → ミッションボード自動生成
    └── personal-orchestrator   パーソナルアシスタント統合オーケストレーター
```

**context-and-impact との関係**: **このカテゴリ全体が context-and-impact のスキルコンステレーション**。C1 がハブで C2〜C5 がスポーク。

---

## [D] OpenClaw クラスター — 10スキル

分散エージェントクラスター（Windows Gateway + 4 ノード）の運用。

```
openclaw-*
│
├── D1 クラスター管理
│   ├── openclaw-agents         エージェント10体の状態確認・メッセージ送信
│   ├── openclaw-agent-sync     TUI/CLI 経由の状態取得・メモリ同期・ブロードキャスト
│   ├── openclaw-bridge         パーソナルアシスタント ↔ Gateway 通信ブリッジ
│   ├── openclaw-cluster-recovery  クラスター復旧手順
│   └── openclaw-integration    mini2/mini3 への Miyabi スキル統合
│
├── D2 コース制作（OpenClaw コースプロダクションライン）
│   ├── openclaw-course-producer   Udemy コース制作（スクリプト・スライド・動画）
│   ├── openclaw-course-manager    コース管理（進捗・品質ゲート・撮影計画）
│   ├── openclaw-course-marketing  マーケティング素材（サムネイル・LP・SNS投稿）
│   ├── openclaw-script-manager    台本管理（作成・編集・レビュー・品質チェック）
│   └── openclaw-slide-gen         スライド画像生成（Gemini API バッチ生成）
│
└── D3 レポート・通知
    └── pen1-report             PEN1 TUI レポート + Telegram 通知 + X ポスト素材
```

---

## [E] ナレッジ / Obsidian — 5スキル

知識グラフ・Obsidian Vault 管理。

```
│
├── obsidian-knowledge      MEMORY/ → Obsidian Vault 同期・ナレッジグラフ化
├── obsidian-gni            [B6 と重複] Vault グラフ検索（L2b の実行基盤）
├── graph-master            ctx-eng ナレッジグラフ最適化
├── knowledge-watcher       ナレッジ監視・更新検知
└── memo-assistant          メモ・ナレッジベース管理
```

**context-and-impact との関係**: L3（SmartConnections）のインデックス対象が Obsidian Vault。`obsidian-knowledge` でVaultを整備することが L3 の品質に直結。

---

## [F] コンテンツ / SNS — 9スキル

X（Twitter）・YouTube・note 等の SNS 運用自動化。

```
│
├── F1 X / Twitter
│   ├── xai-account-ops     xAI API（Grok）でトレンド・ポスト・アカウント分析
│   ├── xai-search          SNS & Tech Intelligence
│   └── twitter-api-v2      X API v2 直接使用（OAuth 2.0）
│
├── F2 YouTube
│   ├── youtube             チャンネル運用（13種ワークフロー）
│   ├── youtube-autopilot   企画→台本→サムネ→撮影→公開 全自動パイプライン
│   └── youtube-growth      成長戦略（SEO・分析・コミュニティ）
│
└── F3 ライティング / note
    ├── shunsuke-note-writer  note 記事執筆（AI/テック/教育分野）
    ├── trend-to-note         X トレンド → note 自動記事生成
    └── content-pipeline      Issue → 生成 → Telegram レビュー → note/X 公開
    └── content-writer        汎用コンテンツ作成支援
```

---

## [G] 音声 / TTS — 8スキル

VOICEVOX・Google Home・音声入出力系。

```
│
├── G1 ローカル読み上げ
│   ├── voicebox-narrator       VOICEVOX TTS（ずんだもん等）全操作
│   ├── announce                Google Home + VoiceBox 同時読み上げ
│   ├── announce-bedroom        寝室スピーカー向け
│   ├── announce-office         オフィス向け
│   └── macbook-local-announce  MacBook ローカルスピーカー
│
├── G2 外部スピーカー連携
│   └── voice-bridge            OpenClaw 応答 → Google Home 自動読み上げ
│
├── G3 音声入力
│   └── voice-transcriber       音声認識（STT）音声ファイル → テキスト
│
└── G4 エンタメ
    ├── voicevox-duet           みやびちゃんとの掛け合いライブ配信モード
    └── spotify                 Spotify 再生制御・プレイリスト管理
```

---

## [H] GitHub / 開発フロー — 7スキル

Issue 駆動開発・CI/CD・公開系。

```
│
├── H1 Issue 駆動開発
│   ├── githubops-workflow   Issue → Branch → PR → Merge → Close 全フロー
│   ├── prompt-request       [auto] Issue → AI 自動実装 → PR
│   └── prompt-request-bus   Prompt Request Bus（Webhook ルーティング）
│
├── H2 プロジェクト管理
│   ├── github-projects-ops  GitHub Projects V2 運用・フィールド管理
│   └── github-marketing     リポジトリ成長戦略（スター・トラフィック・npm DL）
│
└── H3 公開・資産化
    ├── zenn-publish         Zenn 記事 GitHub 連携公開
    └── skill-creator        3プラットフォーム対応スキル作成（Claude/Codex/OpenClaw）
```

---

## [I] Google Workspace — 5スキル

```
├── gmail-assistant         Gmail 未読確認・検索・要約・返信ドラフト
├── gmail-gtd-labeler       Gmail 4アカウント GTD 自動ラベリング
├── google-drive-team-workspace  共有ドライブ作成・チーム同期
├── clasp-gas               GAS clasp CLI 開発・デプロイ（スプレッドシート自動化）
└── gws-workspace           Google Workspace CLI（17サービス統合）
```

---

## [J] 通知 / メッセージング — 5スキル

```
├── telegram-buttons        Telegram Inline Buttons 追加
├── telegram-upload         Telegram ファイル添付送信（画像・動画・音声）
├── pushcut-notifications   iOS Pushcut 通知・ショートカット実行
├── discord-community       PPAL Discord コミュニティ管理
└── discord-ops             雅 Discord 自動運用（ゲート・スコアリング・管理）
```

---

## [K] 開発環境 / インフラ — 6スキル

```
├── K1 ターミナル
│   ├── ghostty             Ghostty ターミナル設定・キーバインド
│   └── yazi-integration    Yazi ファイルマネージャ Tmux 統合
│
├── K2 リモート接続
│   ├── termius-manager     Termius SSH 管理
│   ├── windows-remote      Windows SSH 接続・ファイル転送・コマンド実行
│   └── windows-cluster     Windows 分散クラスター
│
└── K3 Claude Code 環境
    ├── claude-code-ops     Claude Code 起動・permission mode・settings 運用
    └── model-switcher      LLM モデルを Anthropic Claude 系に固定
```

---

## [L] パーソナル / アシスタント — 5スキル

```
├── hayashi-assistant   林駿甫専用パーソナル AI アシスタント（タスク・メモ・GTD）
├── hayashi-cli         林 CLI（hayashi コマンド）エージェント運用
├── schedule-manager    スケジュール・カレンダー管理
├── task-tracker        タスク追跡・管理
└── learning-coach      学習支援・教育
```

---

## [M] ビジネス / 法務 — 4スキル

```
├── company-legal   会社設立・運用・法律
├── e-tax-agent     確定申告（e-Tax）
├── law-api         e-Gov 法令検索 API
└── asset-creation  技術・スキル・プロダクトの体系的資産化
```

---

## [N] 教育 / コース — 2スキル

```
├── ppal-lesson-post        PPAL 週次レッスン動画 Discord 投稿
└── udemy-upload-assistant  Udemy コースアップロード支援
```

---

## [O] クリエイティブ / AI生成 — 3スキル

```
├── nanobanana-pro2         Nano Banana Pro 2 画像生成
├── gen-studio-thumbnail    Gen-Studio CLI サムネイル生成（Gemini）
└── rpg-game-creator        RPG ゲームクリエイター
```

---

## [P] システム管理 — 2スキル

```
├── ssd-archive     外付け SSD 大容量ファイルアーカイブ
└── storage-cleanup PC 全体ストレージクリーンアップ
```

---

## [Q] 外部ツール連携 — 2スキル

```
├── craft-docs  Craft Docs 読み書き・タスク管理・KPI・週次レポート
└── lark-dev    Lark Open Platform 開発支援
```

---

## context-and-impact との関係マップ

```
★ = コアバンドル（SKILL.md の integrates: に既記載）
◎ = 直接連携推奨（未バンドル）
○ = 間接的に関連

Context Assembly Layer
  L0 ARIA project_memory    ← ★ aria-ldd-add
  L1 Glob/Grep              ← (組み込み)
  L2a Code Call Graph       ← ★ gitnexus-impact-analysis
                            ← ◎ gni-ops
                            ← ◎ gitnexus-exploring
  L2b Obsidian wikilink     ← ★ obsidian-gni
                            ← ◎ obsidian-knowledge
  L3 Semantic Search        ← (SmartConnections MCP 組み込み)

Quality Gate
  Phase B                   ← (Context Engineering MCP 組み込み)

Execution Planning
  Phase C DAG               ← ★ gni-first-agent-orchestration
                            ← ★ task-dag-planner

Multi-Agent Execution
  Phase D                   ← ★ multi-agent-orchestration
                            ← ★ agent-teams
                            ← ◎ ai-triad
                            ← ◎ codex-workers
                            ← ◎ miyabi-auto
                            ← ◎ miyabi-omega

Feedback & Self-Improvement
  Phase E                   ← ★ cycle-ops
                            ← ★ self-improving-skills
                            ← ◎ miso（進捗可視化）
                            ← ◎ graph-master（グラフ最適化）

Dispatch & Reporting
  Post-execution            ← ◎ pen1-report
                            ← ◎ miyabi-release
```

---

## バンドル設計（推奨）

### Tier 1: Core Bundle（現在の SKILL.md v3.0.0 に記載済み）

| スキル | カテゴリ | 役割 |
|--------|---------|------|
| gni-first-agent-orchestration | B/C | DAG設計の起点 |
| task-dag-planner | C | タスク依存解決 |
| aria-ldd-add | C | 永続状態・監査ログ |
| cycle-ops | C | フィードバックループ |
| multi-agent-orchestration | C | エージェント統合管理 |
| self-improving-skills | C | 自己改善 |
| gitnexus-impact-analysis | B | L2a blast radius |
| obsidian-gni | B/E | L2b wikilink グラフ |
| agent-teams | C | 並列実行 |

### Tier 2: Extended Bundle（追加バンドル推奨）

| スキル | カテゴリ | 追加理由 |
|--------|---------|---------|
| gni-ops | B | インデックス管理・クエリ実行（L2a 前処理） |
| gitnexus-exploring | B | L2a 探索フェーズ |
| gitnexus-cli | B | インデックス更新 |
| obsidian-knowledge | E | L3 対象 Vault の整備 |
| ai-triad | C | Claude/Codex/Gemini 役割分担指針 |
| codex-workers | C | Phase D Codex 実行詳細 |
| miso | C | Phase D 進捗可視化 |
| graph-master | E | Phase B グラフ品質向上 |
| miyabi-omega | A | Phase A-E と 1:1 対応するパイプライン |
| pen1-report | D | Phase E 完了報告 |

### Tier 3: Operational Context（運用時に参照）

| スキル | カテゴリ | 用途 |
|--------|---------|------|
| miyabi-master | A | 全エージェントのリファレンス |
| miyabi-auto | A | Phase D 自律実行エンジン |
| gitnexus-debugging | B | エラー根本原因特定 |
| gitnexus-refactoring | B | 安全なリファクタリング |
| github-projects-ops | H | Issue/PR 管理 |
| prompt-request | H | [auto] Issue 自動実装 |
| skill-creator | H | スキル自体の作成・改善 |

---

## miyabi 系スキル × context-and-impact の対応表

```
miyabi-* スキル群が context-and-impact の各フェーズとどう対応するか

context-and-impact   ←→   miyabi-* 対応スキル
─────────────────────────────────────────────────────────
Phase A: Context    ─── miyabi-cli-ops（検索オペレーション基盤）
Phase B: Quality    ─── miyabi-doctor（品質チェックの参照パターン）
Phase C: DAG Plan   ─── miyabi-build + miyabi-fix（実装パターン）
Phase D: Execution  ─── miyabi-agent + miyabi-auto + miyabi-omega
Phase E: Audit      ─── miyabi-release + miyabi-skills-mgmt

Overall Lifecycle:
  プロジェクト開始  → miyabi-init → miyabi-install
  日常運用          → miyabi-status → miyabi-run
  リリース          → miyabi-ship → miyabi-release
  自動化            → miyabi-auto（Water Spider = Phase D の自律体）
  最上位統合        → miyabi-omega（6段階 = context-and-impact の 5フェーズ + 報告）
```

---

## 重複・整理候補

| スキルペア | 重複内容 | 推奨 |
|-----------|---------|------|
| miyabi-status + miyabi-doctor | 診断機能が重複 | status = 概要、doctor = 詳細診断で分担 |
| gni-ops + gitnexus-impact-analysis | GNI実行が重複 | gni-ops = CLI操作、impact-analysis = 分析フロー |
| obsidian-gni + obsidian-knowledge | Obsidian操作が重複 | gni = グラフ検索、knowledge = Vault同期 |
| miso + miso-spawn | ほぼ同一領域 | miso = 本体、miso-spawn = sessions_spawn特化 |
| youtube + youtube-autopilot + youtube-growth | YouTube 3系統 | 統合 or タスク別に明確化推奨 |
| announce + announce-bedroom + announce-office | 場所違いの読み上げ | 統合して場所パラメータ化推奨 |

---

## カテゴリ別スキル数サマリー

| カテゴリ | スキル数 | 主要用途 |
|---------|---------|---------|
| A Miyabi CLI | 18 | 開発ライフサイクル全般 |
| B コードインテリジェンス | 11 | コード理解・影響分析 |
| C オーケストレーション | 12 | マルチAI・自律ループ |
| D OpenClaw | 10 | 分散クラスター・コース制作 |
| E ナレッジ | 5 | Obsidian・知識管理 |
| F コンテンツ/SNS | 9 | X・YouTube・note |
| G 音声/TTS | 8 | VOICEVOX・Google Home |
| H GitHub/開発フロー | 7 | Issue駆動・CI/CD |
| I Google Workspace | 5 | Gmail・Drive・GAS |
| J 通知/メッセージング | 5 | Telegram・Discord |
| K 開発環境/インフラ | 6 | ターミナル・SSH |
| L パーソナル | 5 | 林CLI・タスク管理 |
| M ビジネス/法務 | 4 | 法務・税務 |
| N 教育/コース | 2 | PPAL・Udemy |
| O クリエイティブ | 3 | 画像・ゲーム |
| P システム管理 | 2 | ストレージ |
| Q 外部ツール | 2 | Craft・Lark |
| **合計** | **120** | |
