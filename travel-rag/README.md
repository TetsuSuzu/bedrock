# 旅行商品 RAG — Amazon Bedrock ナレッジベース実装

「Bedrock ナレッジベースに旅行商品データを取り込み RAG を構成し、`PerformanceConfigLatency` を最適化（optimized）に設定する」を実現するサンプルコードです。

## 実現していること

| 要件 | 実装箇所 |
|------|---------|
| RAG（検索拡張生成） | `bedrock-agent-runtime` の `retrieve_and_generate`（`ask()`） |
| レイテンシ最適化 | `generationConfiguration` / `orchestrationConfiguration` の `performanceConfig.latency = "optimized"` |
| top-k（取得件数調整） | `vectorSearchConfiguration.numberOfResults` |
| メタデータ絞り込み | `vectorSearchConfiguration.filter`（`--category`） |
| カタログ更新時の同期 | `bedrock-agent` の `start_ingestion_job`（`sync_data_source()`） |
| 引用元の表示 | `response["citations"]` を整形表示 |

## 前提

- ナレッジベース・S3 データソースは作成済み（このリポジトリの `bedrock-knowledge-base-notes.md` 参照）
- 認証情報・リージョンは `~/.aws` に設定済み
- 依存: `pip install boto3`（最新版推奨。`performanceConfig` 対応のため）

## 使い方（PowerShell）

```powershell
# 仮想環境を有効化
.\.venv\Scripts\Activate.ps1

# 環境変数で ID を指定
$env:KB_ID = "XXXXXXXXXX"
$env:DATA_SOURCE_ID = "YYYYYYYYYY"

# 1) カタログを同期してから問い合わせ
python travel_rag.py --sync --query "10万円以内で行ける南国のビーチリゾートは？"

# 2) 問い合わせのみ（top-k と latency を指定）
python travel_rag.py -q "ハネムーン向けの静かな宿は？" --top-k 8 --latency optimized

# 3) メタデータ category=beach で絞り込み
python travel_rag.py -q "おすすめのビーチは？" --category beach
```

## チューニングのポイント

- **latency**: `optimized`（応答速度重視）/ `standard`。「応答時間が長い」苦情には `optimized`。
- **top-k**: 少なく → レイテンシ改善 / 多く → 網羅性向上。精度とのバランスで調整。
- **同期**: 商品カタログ更新後に `--sync` を実行するだけ。モデルの再学習（ファインチューニング）は不要。
- **対応フォーマット**: PDF / テキスト / HTML / CSV など。
