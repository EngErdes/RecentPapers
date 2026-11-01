# TFMamba：超音波溶接欠陥分類のためのMambaを用いた時間・周波数表現学習

**Original Title**: *TFMamba: Time-Frequency Representation Learning with Mamba for Ultrasonic Welding Defect Classification*

> **💡 一言要約**: Mambaで溶接欠陥を高速・高精度に自動判別

| 項目 | 内容 |
|---|---|
| **著者** | R Chen, L Hua, P Hu, J Li |
| **掲載誌** | 11th Asia-Pacific Conference on Intelligent … 2026 |
| **アラートキーワード** | representation learning |
| **原文リンク** | [https://ieeexplore.ieee.org/abstract/document/11741468/](https://ieeexplore.ieee.org/abstract/document/11741468/) |
| **PDF版要約** | [README.pdf](./README.pdf) |

---

## 📊 新規性の図解（先行研究との違いと本研究のブレークスルー）

```mermaid
%%{init: {'flowchart': {'wrappingWidth': 520, 'nodeSpacing': 18, 'rankSpacing': 28, 'padding': 14, 'curve': 'basis'}, 'themeVariables': {'fontSize': '14px'}}}%%
flowchart TD
    S1["<b>【1. 先行研究の限界】 解析精度と計算コストの壁</b><br/>──────────────────────────────<br/>時間と周波数の特徴を同時に扱うと、計算が重くなり実用性に欠けていた。"]
    S2["<b>【2. 本研究の着眼点】 次世代SSMの応用</b><br/>──────────────────────────────<br/>長大なデータでも高速・低メモリで処理できるMambaの特性に着目した。"]
    S3["<b>【3. 技術的な新規性】 TFMambaの独自構造</b><br/>──────────────────────────────<br/>時間軸と周波数軸の情報を効率よく融合して学習する新モデルを構築。"]
    S4["<b>【4. 新規性による優位性】 圧倒的な分類性能と速度</b><br/>──────────────────────────────<br/>従来手法を超える精度を達成し、現場でのリアルタイム診断を可能にした。"]
    S1 --> S2
    S2 --> S3
    S3 --> S4
    style S1 fill:#EFF6FF,stroke:#1E40AF,stroke-width:2px,color:#111827,rx:8,ry:8
    style S2 fill:#F0FDFA,stroke:#0F766E,stroke-width:2px,color:#111827,rx:8,ry:8
    style S3 fill:#F5F3FF,stroke:#6D28D9,stroke-width:2px,color:#111827,rx:8,ry:8
    style S4 fill:#FFF7ED,stroke:#C2410C,stroke-width:2px,color:#111827,rx:8,ry:8
```

## 📝 要約

超音波溶接の品質管理において、時間と周波数の情報を統合的に学習する新しいモデル「TFMamba」を提案しました。最新のState Space ModelであるMambaを採用することで、従来の深層学習モデルよりも効率的かつ高精度に溶接欠陥を分類することが可能です。

## ❓ どんな問題に取り組んだか

超音波溶接の欠陥検出では、信号の時間的な変化と周波数の特徴を同時に捉える必要があります。しかし、従来のCNNやTransformerベースの手法では、計算コストが増大したり、長期間の依存関係を十分にモデル化できなかったりする課題がありました。

## ✨ 何が新しい？何がすごい？（新規性）

本研究は、計算効率に優れた次世代アーキテクチャ「Mamba」を、時間・周波数ドメインの表現学習にはじめて本格導入した点が画期的です。先行研究のTransformerが抱えていた計算量の課題を克服しつつ、Mambaの選択的状態空間モデルにより、ノイズの多い信号から欠陥特有の微細なパターンを抽出することに成功しました。これにより、高い分類精度と推論の高速化を両立しています。

## 🎓 大学1年生向けの解説

金属同士をくっつける「超音波溶接」がうまくいったかどうかを、AIが自動で判断する技術の研究です。溶接中のデータには「いつ」「どんな音（周波数）」が出たかという重要な情報が詰まっていますが、これを分析するのは非常に複雑でした。この論文では、最新の「Mamba」という計算手法を使うことで、まるでベテランの職人のように素早く正確に不良品を見分けるAIを作り上げました。これにより、工場の製造ラインをよりスムーズに、より高品質に保つことができます。
