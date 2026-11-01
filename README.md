# フィリピン保健省の監視データを用いた自己教師あり時系列表現学習による感染症流行予測

**Original Title**: *Self-Supervised Temporal Representation Learning for Infectious Disease Outbreak Prediction Using Philippine DOH Surveillance Data*

> **💡 一言要約**: AIが自律学習し、感染症の流行を予測する

| 項目 | 内容 |
|---|---|
| **著者** | MY Orong, J Matias, ES Ybanez, CZ Cabatingan |
| **掲載誌** | International Conference on … 2026 |
| **アラートキーワード** | representation learning |
| **原文リンク** | [https://ieeexplore.ieee.org/abstract/document/11736797/](https://ieeexplore.ieee.org/abstract/document/11736797/) |
| **PDF版要約** | [README.pdf](./README.pdf) |

---

## 📊 新規性の図解（先行研究との違いと本研究のブレークスルー）

```mermaid
%%{init: {'flowchart': {'wrappingWidth': 520, 'nodeSpacing': 18, 'rankSpacing': 28, 'padding': 14, 'curve': 'basis'}, 'themeVariables': {'fontSize': '14px'}}}%%
flowchart TD
    S1["<b>【1. 先行研究の限界】 ラベル付きデータの不足</b><br/>──────────────────────────────<br/>高品質な正解ラベル付きデータの収集が難しく、従来の学習モデルでは限界があった。"]
    S2["<b>【2. 本研究の着眼点】 自己教師あり学習の活用</b><br/>──────────────────────────────<br/>正解ラベルに頼らず、データそのものの時間的構造から特徴を抽出する手法に着目した。"]
    S3["<b>【3. 技術的な新規性】 DOH-SSLモデルの構築</b><br/>──────────────────────────────<br/>多変量な疫学データに適した独自の時系列表現学習アルゴリズムを設計した。"]
    S4["<b>【4. 新規性による優位性】 自律的な特徴抽出の実現</b><br/>──────────────────────────────<br/>複雑なデータ加工なしで、従来手法を上回る精度でアウトブレイクの予測を可能にした。"]
    S1 --> S2
    S2 --> S3
    S3 --> S4
    style S1 fill:#EFF6FF,stroke:#1E40AF,stroke-width:2px,color:#111827,rx:8,ry:8
    style S2 fill:#F0FDFA,stroke:#0F766E,stroke-width:2px,color:#111827,rx:8,ry:8
    style S3 fill:#F5F3FF,stroke:#6D28D9,stroke-width:2px,color:#111827,rx:8,ry:8
    style S4 fill:#FFF7ED,stroke:#C2410C,stroke-width:2px,color:#111827,rx:8,ry:8
```

## 📝 要約

本研究は、フィリピン保健省の多変量疫学データを解析するために、DOH-SSLと呼ばれる自己教師あり時系列表現学習アプローチを提案しました。このモデルは生の時系列データから有益な特徴を自律的に学習し、感染症のアウトブレイク予測精度を向上させます。

## ❓ どんな問題に取り組んだか

従来の感染症予測手法は、ラベル付きデータの不足や、複雑な多変量時系列データの依存関係を十分に捉えられないという課題がありました。また、膨大な監視データから予測に有用な情報を効率的に抽出する汎用的な手法も不足していました。

## ✨ 何が新しい？何がすごい？（新規性）

本研究の新規性は、自己教師あり学習（Self-Supervised Learning）を多変量疫学データに特化させた「DOH-SSL」を開発した点にあります。ラベルのない生の監視データから時間的な相関関係を直接学習することで、手動の特徴量エンジニアリングを排除しました。フィリピン保健省の実データを用いて、限られた情報下でも高度な表現獲得が可能であることを示した点が大きな貢献です。

## 🎓 大学1年生向けの解説

この研究は、AIを使って「いつ感染症が流行するか」をより正確に当てるための新しい方法を開発したものです。通常、AIの学習には人間が答えを教える必要がありますが、この方法はデータの中からAIが自分でルールを見つけ出す仕組み（自己教師あり学習）を使っています。フィリピンの実際の保健データを使って、難しい準備なしに流行の兆しを掴めるようにしたのがすごいところです。
