# AWS Certified Generative AI — AIP 問題 解説

分野5「AI ソリューションのセキュリティ、コンプライアンス、ガバナンス」など。

---

## AIP-9 — クロスリージョン推論（CRI）と SCP / IAM【2つ選択】

### 状況
- AWS Control Tower のマルチアカウント。**SCP で eu-west-1 以外のリージョンへのアクセスを制限**。
- ML エンジニアが eu-west-1 から EU 向け推論プロファイル `eu.amazon.nova-pro-v1:0` で **クロスリージョン推論（CRI）** を実行。
- エラー: `On resource(s): arn:aws:bedrock:eu-north-1::foundation-model/amazon.nova-pro-v1:0` / `a service control policy explicitly denies the action`

### 根本原因
クロスリージョン推論プロファイル（`eu.` 接頭辞）は、リクエストを **EU 内の複数リージョンに自動で振り分ける**。
エンジニアは eu-west-1 を呼んだつもりでも CRI が実処理を **eu-north-1** にルーティング → SCP が eu-west-1 以外を拒否しているため、`eu-north-1` の InvokeModel が **SCP により明示的に拒否**された。

### 正解（2つ）
1. **SCP に、`eu.amazon.nova-pro-v1:0` の CRI ルーティング先となる EU リージョンでの Bedrock 推論アクションを許可する例外ルールを追加する。**
   - 組織レベルの拒否を解消。データレジデンシー（EU 域内）を維持しつつ EU リージョン群に限定。
2. **ML エンジニアの IAM ポリシーで、推論プロファイルおよび関連する全 EU リージョンの基盤モデルに対する `bedrock:InvokeModel*` が許可されていることを確認する。**
   - 権限は「SCP ∩ IAM の積集合」。SCP を直しても IAM が不足すれば呼べない。

### 誤り
- **PowerUserAccess をアタッチ** → 過剰権限で最小権限違反。かつ問題は IAM 不足でなく SCP の拒否なので解決しない。
- **SCP で `eu.*` 全プロファイルを一括許可** → 範囲が広すぎてガバナンス上不適切。
- **eu-north-1 コンソールでモデルアクセスを個別有効化** → SCP の拒否とは別問題で解決にならない。

### 覚え方
> CRI が SCP 制限環境で失敗 → 「SCP の例外追加」＋「IAM 権限の確認」の両輪。許可は**ルーティング先 EU リージョンに限定**してレジデンシーとガバナンスを守る。

---

## AIP-15 — Prompt Management ＋ Guardrails で運用負荷最小化

### 要件
- 部門（営業・コンプラ・経理）ごとに異なるトーンで回答。
- 統一フォーマット（要点・リスク評価・注意事項）を適用。
- 暴力的/差別的表現の排除＋PII を回答に含めない。
- プロンプトを部門横断で統合管理。
- コンテンツフィルタ基準を運用中に柔軟変更。
- **運用チームの負担を最小限に。**

### 正解：選択肢3
> Bedrock のプロンプト管理（Prompt Management）で共通テンプレートを作成し部門ごとのバリアントを定義。Bedrock のガードレールでコンテンツカテゴリフィルター・単語フィルター・機密情報フィルターを構成して不適切な出力を防止する。

| 要件 | 実現 |
|------|------|
| 部門ごとのトーン | Prompt Management のバリアント |
| 統一フォーマット | 共通テンプレートに定義 |
| プロンプト統合管理 | Prompt Management で一元・バージョン管理 |
| 有害表現の除外 | Guardrails のコンテンツカテゴリ/単語フィルター |
| PII の除外 | Guardrails の機密情報フィルター |
| 運用中の柔軟変更 | 設定変更だけでコード改修不要 |
| 運用負荷最小 | すべてマネージド、カスタムコード不要 |

### 誤り
- **選択肢1**（Prompt Management＋Step Functions＋Guardrails＋Comprehend）: 実現可能だが Step Functions と Comprehend を自前構築・保守。Guardrails で PII/有害表現を賄えるため Comprehend は冗長。運用負荷高。
- **選択肢2**（システムプロンプト埋め込み＋S3 に JSON＋Lambda で Comprehend）: マネージド機能を使わず車輪の再発明。運用負荷大。
- **選択肢4**（SageMaker カスタムモデル＋部門別エンドポイント＋Lambda＋Macie）: 最も運用負荷が高い。Macie は S3 データ検出用でリアルタイム PII 除去に不向き。

### 覚え方
> 「プロンプトの一元管理」＝ Prompt Management、「有害表現・PII フィルタ＋運用中の柔軟変更」＝ Guardrails。この2つの組み合わせがコード不要で運用負荷を最小化する王道。
