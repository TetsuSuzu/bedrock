"""
旅行商品 RAG（検索拡張生成）— Amazon Bedrock ナレッジベース実装サンプル

正解1 の内容を実現するコード:
  - Bedrock ナレッジベースに旅行商品データ（S3）を取り込み RAG を構成
  - RetrieveAndGenerate で問い合わせ
  - PerformanceConfigLatency を 'optimized' に設定して低レイテンシ化
  - top-k（numberOfResults）で検索取得件数を調整

前提:
  - ナレッジベースと S3 データソースは作成済み（KB_ID / DATA_SOURCE_ID を環境変数で指定）
  - 認証情報・リージョンは ~/.aws に設定済み

実行例 (PowerShell):
  $env:KB_ID="XXXXXXXXXX"; $env:DATA_SOURCE_ID="YYYYYYYYYY"
  python travel_rag.py --query "10万円以内で行ける南国のビーチリゾートは？"
"""

from __future__ import annotations

import argparse
import os
import time

import boto3
from botocore.config import Config

# ---- 既定設定 -------------------------------------------------------------

REGION = os.environ.get("AWS_REGION", "ap-northeast-1")

# RAG の生成に使う基盤モデル（ARN または推論プロファイル ARN）
# 例: Claude 3.5 Sonnet
DEFAULT_MODEL_ARN = os.environ.get(
    "MODEL_ARN",
    f"arn:aws:bedrock:{REGION}::foundation-model/anthropic.claude-3-5-sonnet-20240620-v1:0",
)

# レイテンシ最適化: 'optimized'（応答速度重視） / 'standard'
PERFORMANCE_LATENCY = os.environ.get("PERFORMANCE_LATENCY", "optimized")

# top-k: 検索で取得する件数（少→低レイテンシ / 多→高網羅性）
DEFAULT_TOP_K = int(os.environ.get("TOP_K", "5"))


def _client(service: str):
    """リトライ付きの boto3 クライアントを生成。"""
    cfg = Config(region_name=REGION, retries={"max_attempts": 5, "mode": "adaptive"})
    return boto3.client(service, config=cfg)


# ---- データソース同期（商品カタログ更新時に実行）-------------------------

def sync_data_source(kb_id: str, data_source_id: str, wait: bool = True) -> str:
    """
    S3 のデータソースをナレッジベースに取り込む（インジェスションジョブ）。
    商品カタログを更新したら同期するだけで最新データが検索対象になる。
    """
    agent = _client("bedrock-agent")
    resp = agent.start_ingestion_job(
        knowledgeBaseId=kb_id, dataSourceId=data_source_id
    )
    job_id = resp["ingestionJob"]["ingestionJobId"]
    print(f"[sync] ingestion job started: {job_id}")

    if not wait:
        return job_id

    # 完了までポーリング
    while True:
        job = agent.get_ingestion_job(
            knowledgeBaseId=kb_id,
            dataSourceId=data_source_id,
            ingestionJobId=job_id,
        )["ingestionJob"]
        status = job["status"]
        print(f"[sync] status: {status}")
        if status in ("COMPLETE", "FAILED"):
            if status == "FAILED":
                print("[sync] failureReasons:", job.get("failureReasons"))
            else:
                print("[sync] statistics:", job.get("statistics"))
            return status
        time.sleep(5)


# ---- RAG 問い合わせ（RetrieveAndGenerate）--------------------------------

def ask(
    kb_id: str,
    query: str,
    model_arn: str = DEFAULT_MODEL_ARN,
    top_k: int = DEFAULT_TOP_K,
    latency: str = PERFORMANCE_LATENCY,
    metadata_filter: dict | None = None,
) -> dict:
    """
    旅行商品カタログに対して RAG 問い合わせを行う。

    - performanceConfig.latency = 'optimized' で推論レイテンシを最小化
    - vectorSearchConfiguration.numberOfResults = top_k で取得件数を調整
    - metadata_filter で 'category' 等のメタデータ絞り込みも可能
    """
    runtime = _client("bedrock-agent-runtime")

    vector_search: dict = {"numberOfResults": top_k}
    if metadata_filter:
        vector_search["filter"] = metadata_filter

    kb_config = {
        "knowledgeBaseId": kb_id,
        "modelArn": model_arn,
        "retrievalConfiguration": {
            "vectorSearchConfiguration": vector_search
        },
        "generationConfiguration": {
            # 生成（最終応答）のレイテンシ最適化
            "performanceConfig": {"latency": latency},
        },
        "orchestrationConfiguration": {
            # クエリ生成・検索オーケストレーションのレイテンシ最適化
            "performanceConfig": {"latency": latency},
        },
    }

    resp = runtime.retrieve_and_generate(
        input={"text": query},
        retrieveAndGenerateConfiguration={
            "type": "KNOWLEDGE_BASE",
            "knowledgeBaseConfiguration": kb_config,
        },
    )
    return resp


def print_answer(resp: dict) -> None:
    """応答本文と引用元（出典）を整形表示。"""
    print("\n=== 回答 ===")
    print(resp["output"]["text"])

    print("\n=== 引用元（出典）===")
    for i, citation in enumerate(resp.get("citations", []), 1):
        for ref in citation.get("retrievedReferences", []):
            loc = ref.get("location", {})
            uri = (
                loc.get("s3Location", {}).get("uri")
                or loc.get("type")
                or "(unknown)"
            )
            snippet = ref.get("content", {}).get("text", "")[:120]
            print(f"  [{i}] {uri}")
            if snippet:
                print(f"       {snippet}...")


# ---- 低レイテンシ単発呼び出し（参考: RAG なしの素の InvokeModel）---------

def converse_optimized(prompt: str, model_arn: str = DEFAULT_MODEL_ARN,
                       latency: str = PERFORMANCE_LATENCY) -> str:
    """
    参考: Converse API でも performanceConfig.latency を指定できる。
    RAG を介さずモデルを直接呼ぶ場合の最適化例。
    """
    runtime = _client("bedrock-runtime")
    resp = runtime.converse(
        modelId=model_arn,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        performanceConfig={"latency": latency},
    )
    return resp["output"]["message"]["content"][0]["text"]


# ---- CLI -----------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="旅行商品 RAG (Bedrock Knowledge Base)")
    parser.add_argument("--query", "-q", help="ユーザーの質問")
    parser.add_argument("--kb-id", default=os.environ.get("KB_ID"), help="ナレッジベース ID")
    parser.add_argument("--data-source-id", default=os.environ.get("DATA_SOURCE_ID"),
                        help="データソース ID（--sync 時に使用）")
    parser.add_argument("--model-arn", default=DEFAULT_MODEL_ARN, help="生成に使うモデル ARN")
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K, help="検索取得件数")
    parser.add_argument("--latency", default=PERFORMANCE_LATENCY,
                        choices=["optimized", "standard"], help="レイテンシ設定")
    parser.add_argument("--category", help="メタデータ category で絞り込み（例: beach）")
    parser.add_argument("--sync", action="store_true", help="先にデータソースを同期する")
    args = parser.parse_args()

    if not args.kb_id:
        parser.error("KB_ID を --kb-id か環境変数 KB_ID で指定してください")

    if args.sync:
        if not args.data_source_id:
            parser.error("--sync には --data-source-id（または環境変数 DATA_SOURCE_ID）が必要です")
        sync_data_source(args.kb_id, args.data_source_id)

    if not args.query:
        return

    metadata_filter = None
    if args.category:
        metadata_filter = {"equals": {"key": "category", "value": args.category}}

    t0 = time.time()
    resp = ask(
        kb_id=args.kb_id,
        query=args.query,
        model_arn=args.model_arn,
        top_k=args.top_k,
        latency=args.latency,
        metadata_filter=metadata_filter,
    )
    elapsed = time.time() - t0

    print_answer(resp)
    print(f"\n[latency={args.latency}, top_k={args.top_k}] 応答時間: {elapsed:.2f}s")


if __name__ == "__main__":
    main()
