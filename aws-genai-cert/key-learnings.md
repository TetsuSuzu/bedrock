# Key Learnings（重要用語まとめ）

## セット 1

| 用語 / 概念 | 定義 |
|------------|------|
| Model Distillation（モデル蒸留） | 大きなモデルから小さなモデルへ知識を転送する（Teacher-Student） |
| Proximal Policy Optimization (PPO) | 制約付きステップ幅でポリシーを更新する強化学習アルゴリズム（RLHF で使用） |
| Continued Pre-Training（継続的事前学習） | ファインチューニング前に、ドメイン固有データ（ラベルなし）で追加の事前学習を行う |
| ROUGE metric | 参照文との n-gram の重なりでテキスト要約を評価（Recall 寄り） |
| BLEU metric | 予測文と参照文の n-gram を比較し機械翻訳を評価（Precision 寄り） |

## セット 2

| 用語 / 概念 | 定義 |
|------------|------|
| SageMaker HyperPod | 大規模モデル向けの高性能マルチ GPU 学習環境（自己復旧・チェックポイント再開） |
| HNSW (Hierarchical Navigable Small World) | 高速な近似最近傍探索(ANN)のためのグラフベースアルゴリズム |
| Cosine Similarity | ベクトル間の類似度を角度のコサインで測定（大きさに非依存） |
| Amazon DataZone | データの発見・共有・ガバナンスを行う集中型サービス |

---

## 補足：用語の関係整理

```
【モデルを作る・調整する手法】
 ├ Continued Pre-Training … ドメイン知識を足す（ラベルなし）
 ├ Fine-Tuning ………………… 入力→正解で教える（ラベルあり）
 ├ RLHF (PPO) ………………… 人間の好み・安全性に合わせる
 └ Model Distillation ……… 大モデルの知識で小モデルを作る（コスト↓）

【出力を評価する指標】
 ├ ROUGE / BLEU …………… 自動・定量（n-gram 一致、表面的）
 └ Human Evaluation …… 人間・主観（ブランドトーン等）

【ベクトル検索 / RAG の中核】
 ├ HNSW ……………… 近似最近傍探索を高速化するインデックス（探し方）
 └ Cosine Similarity … ベクトルの近さを測る指標（測り方）

【学習基盤 / データ管理】
 ├ SageMaker HyperPod … 大規模分散学習インフラ
 └ Amazon DataZone …… データガバナンスの集中管理
```

## ROUGE / BLEU の弱点（重要）
- 単語の表面的な一致しか見ないため、言い換え・同義語・文脈・自然さを評価できない。
- ブランドトーンや人間らしさなど主観的・創造的品質は測れない → Human Evaluation や LLM-as-a-judge を併用。
- 意味ベースの改良指標: METEOR、BERTScore など。
