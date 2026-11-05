# マルト族の岩面画における顔料分析のための環境光VNIRハイパースペクトルイメージング

**Original Title**: *Ambient light VNIR hyperspectral imaging for pigment analysis in Martu rock art*

> **💡 一言要約**: 自然光とAI解析で岩面画の「色」を解き明かす

| 項目 | 内容 |
|---|---|
| **著者** | A Papasergio, S Mutch, KM Thompson, G Marini… |
| **掲載誌** | npj Heritage Science 2026 |
| **アラートキーワード** | independent component ... |
| **PDF** | [https://www.nature.com/articles/s40494-026-03089-z_reference.pdf](https://www.nature.com/articles/s40494-026-03089-z_reference.pdf) |
| **原文リンク** | [https://www.nature.com/articles/s40494-026-03089-z_reference.pdf](https://www.nature.com/articles/s40494-026-03089-z_reference.pdf) |
| **PDF版要約** | [README.pdf](./README.pdf) |

---

## 📊 新規性の図解（先行研究との違いと本研究のブレークスルー）

```mermaid
%%{init: {'flowchart': {'wrappingWidth': 520, 'nodeSpacing': 18, 'rankSpacing': 28, 'padding': 14, 'curve': 'basis'}, 'themeVariables': {'fontSize': '14px'}}}%%
flowchart TD
    S1["<b>【1. 先行研究の限界】 分析に伴う毀損と機材の制約</b><br/>──────────────────────────────<br/>岩面画のサンプリングによる損傷や、調査現場への大型照明機材の持ち込みが困難であった。"]
    S2["<b>【2. 本研究の着眼点】 環境光を活用した現場撮影</b><br/>──────────────────────────────<br/>人工光源を使わず、自然光のみでVNIRハイパースペクトル撮影を行う簡便なワークフローを構築。"]
    S3["<b>【3. 技術的な新規性】 MNFとICAによる高度解析</b><br/>──────────────────────────────<br/>ノイズを低減するMNF変換と、混ざった成分を分離するICAを組み合わせたデータ処理手法。"]
    S4["<b>【4. 新規性による優位性】 非破壊での高精度顔料識別</b><br/>──────────────────────────────<br/>肉眼では見えない顔料の重なりや、岩の背景に埋もれた微細な模様を鮮明に抽出することに成功。"]
    S1 --> S2
    S2 --> S3
    S3 --> S4
    style S1 fill:#EFF6FF,stroke:#1E40AF,stroke-width:2px,color:#111827,rx:8,ry:8
    style S2 fill:#F0FDFA,stroke:#0F766E,stroke-width:2px,color:#111827,rx:8,ry:8
    style S3 fill:#F5F3FF,stroke:#6D28D9,stroke-width:2px,color:#111827,rx:8,ry:8
    style S4 fill:#FFF7ED,stroke:#C2410C,stroke-width:2px,color:#111827,rx:8,ry:8
```

## 📝 要約

オーストラリアのマルト族の岩面画を対象に、自然光（環境光）を用いた可視・近赤外（VNIR）ハイパースペクトル撮影による非破壊的な顔料分析手法を提案した。MNF変換と独立成分分析（ICA）を組み合わせることで、複雑な地質背景から顔料情報を高精度に分離・抽出することに成功している。

## ❓ どんな問題に取り組んだか

岩面画の分析において、物理的なサンプル採取は文化遺産の毀損につながるため厳しく制限される。また、従来のハイパースペクトル撮影は強力な人工光源を必要とすることが多く、遠隔地の過酷な環境にある遺跡での実施は技術的・物流的に困難であった。

## ✨ 何が新しい？何がすごい？（新規性）

人工照明を使用せず、変動しやすい環境光下での撮影データから高精度な情報を抽出するプロセスを確立した点が画期的である。MNFでノイズを抑えつつ、ICAによって重なり合った顔料や背景の岩石成分を独立した画像として分離することで、肉眼では判別不能な微細な顔料の分布を可視化し、先行研究よりも簡便かつ詳細な分析を可能にした。

## 🎓 大学1年生向けの解説

大昔の岩壁に描かれた絵を、壊したり触れたりせずに詳しく調べる技術についての研究です。特別なカメラで「光の波長」を細かく分けることで、使われている絵の具の種類を特定します。これまでは夜間に大きなライトを当てて撮影する必要がありましたが、この方法なら太陽の光だけで、重なって描かれた絵や消えかかった模様もはっきりと見つけ出すことができます。
