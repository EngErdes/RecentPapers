# ボランティアの希望を考慮した割り当て問題への回答セットプログラミングとメタヒューリスティクスの適用

**Original Title**: *Applying Answer Set Programming and Metaheuristics to the Volunteer Assignment Problem with Preferences*

> **💡 一言要約**: AIと最適化手法でボランティアの希望を最大化

| 項目 | 内容 |
|---|---|
| **著者** | FR Dutra, TP Valente, CV Araújo, AM Arruda |
| **掲載誌** | Encontro Nacional de Inteligência … 2026 |
| **アラートキーワード** | generalized assignment ... |
| **PDF** | [https://sol.sbc.org.br/index.php/eniac/article/download/47079/46836](https://sol.sbc.org.br/index.php/eniac/article/download/47079/46836) |
| **Git リポジトリ** | [https://github.com/FRianOD/VAP-Artigo](https://github.com/FRianOD/VAP-Artigo) |
| **原文リンク** | [https://sol.sbc.org.br/index.php/eniac/article/download/47079/46836](https://sol.sbc.org.br/index.php/eniac/article/download/47079/46836) |
| **PDF版要約** | [README.pdf](./README.pdf) |

---

## 📊 新規性の図解（先行研究との違いと本研究のブレークスルー）

```mermaid
%%{init: {'flowchart': {'wrappingWidth': 520, 'nodeSpacing': 18, 'rankSpacing': 28, 'padding': 14, 'curve': 'basis'}, 'themeVariables': {'fontSize': '14px'}}}%%
flowchart TD
    S1["<b>【1. 先行研究の限界】 計算時間の壁</b><br/>──────────────────────────────<br/>複雑な希望条件が増えると、従来の計算手法では解を出すのに時間がかかりすぎる。"]
    S2["<b>【2. 本研究の着眼点】 論理と探索の融合</b><br/>──────────────────────────────<br/>厳密なルールを守る論理プログラミングと、効率的に探す手法を組み合わせて解決を図る。"]
    S3["<b>【3. 技術的な新規性】 3つの最適化戦略</b><br/>──────────────────────────────<br/>回答セットプログラミングとメタヒューリスティクスを掛け合わせた3種の戦略を考案。"]
    S4["<b>【4. 新規性による優位性】 満足度と速さの両立</b><br/>──────────────────────────────<br/>ボランティアの希望を最大限に叶えつつ、実用的な時間内での割り当てを実現した。"]
    S1 --> S2
    S2 --> S3
    S3 --> S4
    style S1 fill:#EFF6FF,stroke:#1E40AF,stroke-width:2px,color:#111827,rx:8,ry:8
    style S2 fill:#F0FDFA,stroke:#0F766E,stroke-width:2px,color:#111827,rx:8,ry:8
    style S3 fill:#F5F3FF,stroke:#6D28D9,stroke-width:2px,color:#111827,rx:8,ry:8
    style S4 fill:#FFF7ED,stroke:#C2410C,stroke-width:2px,color:#111827,rx:8,ry:8
```

## 📝 要約

ボランティアの希望を最大限に反映しつつ最適な配置を決定する「ボランティア割り当て問題」に対し、計算効率を高める手法を提案した研究です。NP困難とされる複雑な組み合わせ問題に対し、回答セットプログラミング（ASP）とメタヒューリスティクスを組み合わせた3つの戦略を評価し、実用的な解決策を示しています。

## ❓ どんな問題に取り組んだか

ボランティアの割り当ては、参加者の多様な希望や制約を考慮する必要があり、組み合わせが膨大になるため計算が非常に困難（NP困難）です。これまでの総当たり的な手法では、現実的な時間内に最適な配置を見つけることができず、運営上の大きな課題となっていました。

## ✨ 何が新しい？何がすごい？（新規性）

論理的な制約を厳密に扱う回答セットプログラミング（ASP）と、広大な探索空間を効率的に調べるメタヒューリスティクスを融合させた点が最大の特徴です。ボランティアの満足度（希望の合致）を最大化するために、3つの異なる計算戦略を比較評価することで、精度の高い解を高速に導き出すフレームワークを構築しました。これにより、複雑な人間系の制約と数学的な最適化を同時に実現する新しいアプローチを提示しています。

## 🎓 大学1年生向けの解説

ボランティアのイベントで「誰がどの仕事をしたいか」という希望を全員分叶えるのは、パズルを解くように非常に難しい作業です。この研究では、コンピュータに「守るべきルール」と「みんなの希望」を教え、賢く答えを探させる特別なプログラム（ASPとメタヒューリスティクス）を開発しました。これを使えば、何千通りもある組み合わせの中から、みんなが一番ハッピーになれる配置図をあっという間に作ることができます。
