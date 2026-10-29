# DeepASMR：大規模言語モデルを用いたゼロショットASMR音声生成

**Original Title**: *DeepASMR: LLM-Based Zero-Shot ASMR Speech Generation*

> **💡 一言要約**: LLMでASMR音声を自在に生成

| 項目 | 内容 |
|---|---|
| **著者** | L Zhang, T Zhou, H Sun, M Bi, Y Qian |
| **掲載誌** | IEEE Transactions on Audio, Speech and Language Processing 2026 |
| **アラートキーワード** | zero shot |
| **原文リンク** | [https://ieeexplore.ieee.org/abstract/document/11623470/](https://ieeexplore.ieee.org/abstract/document/11623470/) |
| **PDF版要約** | [README.pdf](./README.pdf) |

---

## 📊 新規性の図解（先行研究との違いと本研究のブレークスルー）

```mermaid
%%{init: {'flowchart': {'wrappingWidth': 520, 'nodeSpacing': 18, 'rankSpacing': 28, 'padding': 14, 'curve': 'basis'}, 'themeVariables': {'fontSize': '14px'}}}%%
flowchart TD
    S1["<b>【1. 先行研究の限界】 従来のボトルネック</b><br/>──────────────────────────────<br/>ASMR音声はリラクゼーションや集中力向上に広く活用されているが、特定のASMRスタイル（ささやき声や特徴的な音質）を自動生成する技術は未発達であった。特に、未知の話者に対してもA"]
    S2["<b>【2. 本研究の着眼点】 核心アイデア</b><br/>──────────────────────────────<br/>LLMでASMR音声を自在に生成"]
    S3["<b>【3. 技術的な新規性】 先行研究との違い・工夫</b><br/>──────────────────────────────<br/>LLMの豊富な言語表現能力をASMR特有の音響スタイル制御と組み合わせることで、参照音声のみから未知の話者のASMRスタイルを高精度に再現できる。"]
    S4["<b>【4. 新規性による優位性】 主要な貢献・ブレークスルー</b><br/>──────────────────────────────<br/>実験結果では、自然性とスタイル表現の両面において従来手法を上回る最先端の性能を達成している。"]
    S1 --> S2
    S2 --> S3
    S3 --> S4
    style S1 fill:#EFF6FF,stroke:#1E40AF,stroke-width:2px,color:#111827,rx:8,ry:8
    style S2 fill:#F0FDFA,stroke:#0F766E,stroke-width:2px,color:#111827,rx:8,ry:8
    style S3 fill:#F5F3FF,stroke:#6D28D9,stroke-width:2px,color:#111827,rx:8,ry:8
    style S4 fill:#FFF7ED,stroke:#C2410C,stroke-width:2px,color:#111827,rx:8,ry:8
```

## 📝 要約

本論文では、ASMRスタイルの音声をゼロショット（未知の話者でも参照音声のみで適応可能）で生成する初のフレームワーク「DeepASMR」を提案している。大規模言語モデル（LLM）を活用することで、高い自然性とASMRスタイルの再現を同時に実現する。広範な実験により、提案手法が最先端の自然性とスタイル表現において優れた性能を示すことが確認された。

## ❓ どんな問題に取り組んだか

ASMR音声はリラクゼーションや集中力向上に広く活用されているが、特定のASMRスタイル（ささやき声や特徴的な音質）を自動生成する技術は未発達であった。特に、未知の話者に対してもASMRスタイルを適応させる「ゼロショット話者適応」は大きな技術的課題として残されていた。

## ✨ 何が新しい？何がすごい？（新規性）

DeepASMRはASMR音声生成に特化した世界初のゼロショット対応フレームワークであり、既存の音声合成研究ではほとんど扱われていないASMRというニッチながら需要の高い領域を開拓した。LLMの豊富な言語表現能力をASMR特有の音響スタイル制御と組み合わせることで、参照音声のみから未知の話者のASMRスタイルを高精度に再現できる。実験結果では、自然性とスタイル表現の両面において従来手法を上回る最先端の性能を達成している。

## 🎓 大学1年生向けの解説

ASMRとは、ささやき声や自然音など、聴くとリラックスできる特殊な音声コンテンツのことです。この研究では、そのようなASMR音声をAIが自動で作り出す仕組みを初めて開発しました。特に「ゼロショット」という技術を使い、AIが一度も学習したことのない人の声でも、少しサンプル音声を聞かせるだけでASMRスタイルに変換できます。ChatGPTのような大規模言語モデルの技術を音声生成に応用することで、自然で高品質なASMR音声を生み出すことに成功しました。
