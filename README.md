# AIを活用した世界のLNG運搬船の温室効果ガス定量化と脱炭素化：クリーンな海上物流のためのサロゲートモデル

**Original Title**: *AI-enabled greenhouse gas quantification and targeted decarbonization of the global LNG carrier fleet: a surrogate modeling approach for cleaner maritime logistics*

> **💡 一言要約**: AIで世界のLNG船の排出量を可視化し脱炭素を加速

| 項目 | 内容 |
|---|---|
| **著者** | HA Saddiqi, NA Al-Azri, MA Qyyum |
| **掲載誌** | Cleaner Logistics and Supply Chain 2026 |
| **アラートキーワード** | logistics |
| **原文リンク** | [https://www.sciencedirect.com/science/article/pii/S2772390926000909](https://www.sciencedirect.com/science/article/pii/S2772390926000909) |
| **PDF版要約** | [README.pdf](./README.pdf) |

---

## 📊 新規性の図解（先行研究との違いと本研究のブレークスルー）

```mermaid
%%{init: {'flowchart': {'wrappingWidth': 520, 'nodeSpacing': 18, 'rankSpacing': 28, 'padding': 14, 'curve': 'basis'}, 'themeVariables': {'fontSize': '14px'}}}%%
flowchart TD
    S1["<b>【1. 先行研究の限界】 計算コストと精度の壁</b><br/>──────────────────────────────<br/>物理モデルは正確だが計算が重く、艦隊全体のリアルタイム分析が困難だった。"]
    S2["<b>【2. 本研究の着眼点】 サロゲートモデルの導入</b><br/>──────────────────────────────<br/>AIを用いて複雑な計算を簡略化した「身代わりモデル」を作り、高速化を目指した。"]
    S3["<b>【3. 技術的な新規性】 艦隊規模の分析枠組み</b><br/>──────────────────────────────<br/>個別の船だけでなく、世界中のLNG船団全体を瞬時に定量化できるAI枠組みを構築。"]
    S4["<b>【4. 新規性による優位性】 戦略的脱炭素化の実現</b><br/>──────────────────────────────<br/>どの船を優先的に改善すべきかというデータ駆動型の意思決定が容易になった。"]
    S1 --> S2
    S2 --> S3
    S3 --> S4
    style S1 fill:#EFF6FF,stroke:#1E40AF,stroke-width:2px,color:#111827,rx:8,ry:8
    style S2 fill:#F0FDFA,stroke:#0F766E,stroke-width:2px,color:#111827,rx:8,ry:8
    style S3 fill:#F5F3FF,stroke:#6D28D9,stroke-width:2px,color:#111827,rx:8,ry:8
    style S4 fill:#FFF7ED,stroke:#C2410C,stroke-width:2px,color:#111827,rx:8,ry:8
```

## 📝 要約

本研究は、AIを用いたサロゲートモデル（代替モデル）により、世界のLNG運搬船から排出される温室効果ガスを正確かつ迅速に定量化する手法を提案しています。このモデルを活用することで、個別の船舶や艦隊全体の排出特性を把握し、より効果的な脱炭素化戦略を立てることが可能になります。

## ❓ どんな問題に取り組んだか

LNG輸送の拡大に伴い、海上輸送による温室効果ガス（GHG）排出の把握が急務となっています。しかし、従来の物理ベースの計算モデルは複雑で計算コストが高く、艦隊全体を対象としたリアルタイムの定量化や将来予測を行うのが困難でした。

## ✨ 何が新しい？何がすごい？（新規性）

本研究は、複雑な物理モデルをAI（サロゲートモデル）で近似することで、高精度を維持しつつ計算時間を劇的に短縮した点が画期的です。先行研究では個別のケーススタディに留まることが多かったのに対し、本研究はグローバルなLNG船団全体を対象としたスケーラブルな分析フレームワークを構築しました。これにより、特定の船舶をターゲットにした効率的な脱炭素化施策の選定が可能になります。

## 🎓 大学1年生向けの解説

天然ガスを運ぶ大きな船（LNG船）は、地球温暖化の原因となるガスを排出します。これまでは、その排出量を正確に計算するのに膨大な時間がかかっていました。この研究では、AIを使うことで「計算の手抜き（賢い近似）」を可能にし、世界中の船がどれくらいガスを出しているか一瞬でわかるようにしました。これによって、どの船から対策を始めれば効率よく地球に優しくなれるかが明確になります。
