# ベイズMCMC推論を用いたダンス競技における潜在的なファン投票分布の復元

**Original Title**: *Reconstruction of latent fan vote distributions in dance competitions via Bayesian MCMC inference*

> **💡 一言要約**: 統計学でダンス投票の「裏側」を読み解く

| 項目 | 内容 |
|---|---|
| **著者** | Y Meng |
| **掲載誌** | … Conference on Algorithms, Image Processing, and … 2026 |
| **アラートキーワード** | MCMC |
| **原文リンク** | [https://www.spiedigitallibrary.org/conference-proceedings-of-spie/14504/145042A/Reconstruction-of-latent-fan-vote-distributions-in-dance-competitions-via/10.1117/12.3129753.short](https://www.spiedigitallibrary.org/conference-proceedings-of-spie/14504/145042A/Reconstruction-of-latent-fan-vote-distributions-in-dance-competitions-via/10.1117/12.3129753.short) |
| **PDF版要約** | [README.pdf](./README.pdf) |

---

## 📊 新規性の図解（先行研究との違いと本研究のブレークスルー）

```mermaid
%%{init: {'flowchart': {'wrappingWidth': 520, 'nodeSpacing': 18, 'rankSpacing': 28, 'padding': 14, 'curve': 'basis'}, 'themeVariables': {'fontSize': '14px'}}}%%
flowchart TD
    S1["<b>【1. 先行研究の限界】 投票プロセスのブラックボックス化</b><br/>──────────────────────────────<br/>最終結果しか分からず、投票者の具体的な支持分布を推測する手法が不足していた。"]
    S2["<b>【2. 本研究の着眼点】 ベイズ逆シミュレーションの導入</b><br/>──────────────────────────────<br/>観測データからその発生源となった分布を逆算するという確率的なアプローチを採用。"]
    S3["<b>【3. 技術的な新規性】 MCMCによる潜在分布のサンプリング</b><br/>──────────────────────────────<br/>MCMC法を用いて複雑なパラメータ空間を探索し、最もらしい投票分布を精密に推定。"]
    S4["<b>【4. 新規性による優位性】 潜在的なファン行動の可視化</b><br/>──────────────────────────────<br/>公開データのみから、隠れた投票傾向や支持の偏りを具体的な数値として復元可能にした。"]
    S1 --> S2
    S2 --> S3
    S3 --> S4
    style S1 fill:#EFF6FF,stroke:#1E40AF,stroke-width:2px,color:#111827,rx:8,ry:8
    style S2 fill:#F0FDFA,stroke:#0F766E,stroke-width:2px,color:#111827,rx:8,ry:8
    style S3 fill:#F5F3FF,stroke:#6D28D9,stroke-width:2px,color:#111827,rx:8,ry:8
    style S4 fill:#FFF7ED,stroke:#C2410C,stroke-width:2px,color:#111827,rx:8,ry:8
```

## 📝 要約

ダンス競技における不透明な投票プロセスを解明するため、ベイズ統計学とMCMC（マルコフ連鎖モンテカルロ法）を用いた逆シミュレーション枠組みを提案しています。これにより、最終結果から逆算して、観測不可能なファンの支持傾向や投票分布を精度高く復元することが可能になりました。

## ❓ どんな問題に取り組んだか

ダンス競技では最終的な順位や得点のみが公表されることが多く、投票者が実際にどのような分布で支持を表明していたかという詳細は隠されています。これまでの分析手法では、このような複雑で潜在的な投票行動を正確にモデル化し、背後にあるファンの嗜好を捉えることが困難でした。

## ✨ 何が新しい？何がすごい？（新規性）

本研究は、ダンス競技の投票分析にベイズ逆シミュレーションとMCMCサンプリングを導入した点に大きな新規性があります。従来の統計手法では扱いきれなかった複雑な投票プロセスを確率的な分布として再構築し、個別の投票データがなくても集計データから「ファンの熱量の偏り」を特定できる仕組みを構築したことが主要な貢献です。

## 🎓 大学1年生向けの解説

ダンス大会の順位表だけを見ても、「一部の熱狂的なファンが押し上げたのか」それとも「全員が平均的に良いと評価したのか」という投票の内訳は分かりません。この研究では、数学的なシミュレーションを使って、隠された投票のバランスを逆算して導き出す方法を開発しました。これを使うことで、大会の結果からファンの隠れた心理や応援の傾向を詳しく分析できるようになります。
