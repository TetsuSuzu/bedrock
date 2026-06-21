# Bedrock ナレッジベース / OpenSearch Serverless 調査・作業メモ

## Q. ナレッジベース作成時に自動作成されるのは OpenSearch Service か？

**A. 正確には「Amazon OpenSearch _Serverless_」**（プロビジョンド型の OpenSearch Service ではない）。

- Quick create でベクトルストアを指定しない場合、従来は **OpenSearch Serverless のベクトルコレクション**が自動作成される。
- OpenSearch Serverless は OCU（OpenSearch Compute Unit）単位で課金され、放置すると常時課金が発生しやすい点に注意。

### Bedrock KB が対応するベクトルストア
- Amazon OpenSearch Serverless（デフォルト/自動作成）
- Amazon OpenSearch Service（手動指定）
- Amazon Aurora PostgreSQL (pgvector) / RDS
- Amazon Neptune Analytics
- Pinecone / Redis Enterprise Cloud / MongoDB Atlas（サードパーティ）

## コンソールでの確認場所
1. **Bedrock コンソール** → Builder tools → Knowledge Bases → 対象 KB → 「Vector store」セクション（コレクション ARN / インデックス名）
2. **OpenSearch Service コンソール** → Serverless → Collections（実体・OCU・ポリシー）
3. **Cost Explorer / Billing** → サービス「Amazon OpenSearch Service」、Usage Type に `OCU` を含む項目が Serverless 課金

## CLI での確認
```bash
aws bedrock-agent list-knowledge-bases
aws bedrock-agent get-knowledge-base --knowledge-base-id <KB_ID>
aws opensearchserverless list-collections
```

---

## 実機作業ログ（2026-06-21〜22）

対象アカウント: `691665347318` / リージョン: `ap-northeast-1`

### 環境上の注意（SSL）
- 社内環境の TLS インスペクションにより、AWS CLI が `CERTIFICATE_VERIFY_FAILED` で接続不可。
- 本作業に限り `--no-verify-ssl` で実行（恒久対応は社内 CA を `AWS_CA_BUNDLE` に設定するのが正攻法）。

### 対象 KB
- 名前: `knowledge-base-quick-start-5bru7`
- ID: `ZQRGDPMDJF`
- **type: `MANAGED`**（Bedrock 完全マネージド型。`storageConfiguration` を持たない）

### 重要な発見
- この MANAGED タイプ KB は **顧客アカウント内に独立した OpenSearch Serverless コレクションを作成しない**。
- `aws opensearchserverless list-collections` の結果は空（`collectionSummaries: []`）。
  → 削除すべき OpenSearch Serverless リソースは存在せず、その分の課金もなし。
- 従来の「quick create が OpenSearch Serverless を自動作成する」挙動とは異なる点に注意。

### 実施した操作
1. `aws bedrock-agent delete-knowledge-base --knowledge-base-id ZQRGDPMDJF` → status: DELETING
2. 自動生成された IAM サービスロール `AmazonBedrockExecutionRoleForKnowledgeBase_5bru7` は KB 削除後に別途クリーンアップ（不要のため削除）。

### 教訓
- KB のタイプ（MANAGED か、顧客管理のベクトルストアか）で、付随リソースと課金・削除手順が変わる。
- KB を削除しても、自動生成された IAM サービスロールは残るため別途削除が必要。
