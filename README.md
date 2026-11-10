# AREMamba: 脳波のノイズ除去と感情計算を統合したアーティファクトに強いEmotion Mamba

**Original Title**: *AREMamba: Artifact-Robust Emotion Mamba for Unified EEG Denoising and Affective Computing*

> **💡 一言要約**: ノイズに負けない！次世代Mambaで脳波から感情を解読

| 項目 | 内容 |
|---|---|
| **著者** | W Dong, Z Gong, X Xu, F Wei, L Zhuo |
| **掲載誌** | Proceedings of the 34th ACM International … 2026 |
| **アラートキーワード** | affective computing |
| **原文リンク** | [https://dl.acm.org/doi/abs/10.1145/3767308.3836370](https://dl.acm.org/doi/abs/10.1145/3767308.3836370) |
| **PDF版要約** | [README.pdf](./README.pdf) |

---

## 📊 新規性の図解（先行研究との違いと本研究のブレークスルー）

```mermaid
%%{init: {'flowchart': {'wrappingWidth': 520, 'nodeSpacing': 18, 'rankSpacing': 28, 'padding': 14, 'curve': 'basis'}, 'themeVariables': {'fontSize': '14px'}}}%%
flowchart TD
    S1["<b>【1. 先行研究の限界】 除去と分類のステップ分離</b><br/>──────────────────────────────<br/>ノイズ除去と感情推定が別々に行われ、情報の欠落や計算遅延が生じていた。"]
    S2["<b>【2. 本研究の着眼点】 Mambaによる一気通貫処理</b><br/>──────────────────────────────<br/>長距離の時系列を効率よく扱えるMambaを用い、ノイズ耐性と分類を統合。"]
    S3["<b>【3. 技術的な新規性】 耐ノイズ型特徴抽出モジュール</b><br/>──────────────────────────────<br/>ノイズを識別しつつ感情に重要な信号を抽出する、新しいモデル構造を設計。"]
    S4["<b>【4. 新規性による優位性】 過酷な環境での高精度達成</b><br/>──────────────────────────────<br/>複雑なノイズ環境下でも、低負荷かつTransformerを超える推定精度を実現。"]
    S1 --> S2
    S2 --> S3
    S3 --> S4
    style S1 fill:#EFF6FF,stroke:#1E40AF,stroke-width:2px,color:#111827,rx:8,ry:8
    style S2 fill:#F0FDFA,stroke:#0F766E,stroke-width:2px,color:#111827,rx:8,ry:8
    style S3 fill:#F5F3FF,stroke:#6D28D9,stroke-width:2px,color:#111827,rx:8,ry:8
    style S4 fill:#FFF7ED,stroke:#C2410C,stroke-width:2px,color:#111827,rx:8,ry:8
```

## 📝 要約

脳波（EEG）信号に含まれるノイズ（アーティファクト）を除去しつつ、高精度な感情推定を同時に行う「AREMamba」を提案しています。最新のMambaアーキテクチャを活用し、ノイズ耐性の高い特徴抽出と感情分類を一つのモデルで効率的に実現しました。

## ❓ どんな問題に取り組んだか

脳波信号は時間解像度が高く感情推定に適していますが、まばたきや筋肉の動きといったノイズが混入しやすく、精度の低下を招きます。これまでの手法はノイズ除去と分類を別工程で行うものが多く、情報の損失や処理の複雑さが課題でした。

## ✨ 何が新しい？何がすごい？（新規性）

長距離データの処理に優れたState Space Model（Mamba）を脳波解析に導入し、ノイズ除去と感情分類を統合したエンドツーエンドの学習を実現しました。アーティファクトの影響を抑えるための頑健な特徴抽出モジュールを設計し、計算コストを抑えつつ高い精度を達成しています。これにより、従来のTransformerベースの手法と比較して、より実用的で堅牢な感情コンピューティングの基盤を構築しました。

## 🎓 大学1年生向けの解説

脳波を使って人の感情を読み取る技術の研究です。脳波には「まばたき」などのノイズが混じりやすく、これまでは正確な感情を当てるのが困難でした。この研究では、最新のAI技術を使って、ノイズを自動的に取り除きながら感情をピタリと当てる仕組みを開発しました。これにより、日常生活のようなノイズが多い場面でも、正しく人の気持ちを理解するコンピュータの実現に近づきました。
