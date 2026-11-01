# 船舶追跡のためのデータセットとベンチマーク：海域MOTおよびReIDにおける最新動向の概説

**Original Title**: *A Dataset and Benchmark for Maritime Vessel Tracking with an Overview of Recent Advances in Maritime MOT and ReID*

> **💡 一言要約**: 船舶追跡を革新する新データセットと評価基盤

| 項目 | 内容 |
|---|---|
| **著者** | M Fabijanić, F Ferreira |
| **掲載誌** | 2026 |
| **アラートキーワード** | Multi Camera Tracking |
| **PDF** | [https://skoge.folk.ntnu.no/prost/proceedings/ifac2026_IFACWC26_preprints/files/2021.pdf](https://skoge.folk.ntnu.no/prost/proceedings/ifac2026_IFACWC26_preprints/files/2021.pdf) |
| **Git リポジトリ** | [https://github.com/mf1999/MOT-Sibenik-Dataset](https://github.com/mf1999/MOT-Sibenik-Dataset) |
| **原文リンク** | [https://skoge.folk.ntnu.no/prost/proceedings/ifac2026_IFACWC26_preprints/files/2021.pdf](https://skoge.folk.ntnu.no/prost/proceedings/ifac2026_IFACWC26_preprints/files/2021.pdf) |
| **PDF版要約** | [README.pdf](./README.pdf) |

---

## 📊 新規性の図解（先行研究との違いと本研究のブレークスルー）

```mermaid
%%{init: {'flowchart': {'wrappingWidth': 520, 'nodeSpacing': 18, 'rankSpacing': 28, 'padding': 14, 'curve': 'basis'}, 'themeVariables': {'fontSize': '14px'}}}%%
flowchart TD
    S1["<b>【1. 先行研究の限界】 船舶用データの不足</b><br/>──────────────────────────────<br/>高精度な注釈付きデータが少なく、海域特有の課題への対応が困難だった。"]
    S2["<b>【2. 本研究の着眼点】 固定カメラによる収集</b><br/>──────────────────────────────<br/>海岸線の固定カメラから収集したリアルな船舶映像をデータセット化。"]
    S3["<b>【3. 技術的な新規性】 最新手法の評価基盤</b><br/>──────────────────────────────<br/>4つの主要追跡アルゴリズムを適用し、船舶特有の挙動に対する性能を評価。"]
    S4["<b>【4. 新規性による優位性】 追跡精度の向上に寄与</b><br/>──────────────────────────────<br/>船舶の再識別や長期追跡における新たな基準を確立し、開発効率を向上。"]
    S1 --> S2
    S2 --> S3
    S3 --> S4
    style S1 fill:#EFF6FF,stroke:#1E40AF,stroke-width:2px,color:#111827,rx:8,ry:8
    style S2 fill:#F0FDFA,stroke:#0F766E,stroke-width:2px,color:#111827,rx:8,ry:8
    style S3 fill:#F5F3FF,stroke:#6D28D9,stroke-width:2px,color:#111827,rx:8,ry:8
    style S4 fill:#FFF7ED,stroke:#C2410C,stroke-width:2px,color:#111827,rx:8,ry:8
```

## 📝 要約

海岸線に設置された固定カメラを用いて収集された、新しい船舶用マルチオブジェクト追跡（MOT）データセットを提案し、船舶追跡のロバスト性を向上させるための基盤を提供しています。主要な4つの追跡アルゴリズムをこのデータセットでベンチマーク評価し、海域におけるMOTおよび再識別（ReID）技術の最新の進歩を包括的にまとめています。

## ❓ どんな問題に取り組んだか

海域での船舶追跡は、波の反射や気象条件、船舶同士の重なりといった特有の困難がありますが、研究に活用できる注釈付きの高品質なデータセットが不足していました。また、既存の汎用的な追跡アルゴリズムが、こうした海域特有の課題に対してどの程度の性能を発揮できるかという標準的な評価も不十分でした。

## ✨ 何が新しい？何がすごい？（新規性）

海岸に固定されたカメラから撮影された独自の高品質な注釈付きデータセットを新たに構築し、公開した点が最大の貢献です。さらに、最新のマルチオブジェクト追跡（MOT）と再識別（ReID）の技術動向を海域監視の視点で体系化し、4つの代表的なアルゴリズムを船舶追跡の文脈で比較評価しました。これにより、船舶の動特性に特化したアルゴリズム開発のための明確な指標を確立しました。

## 🎓 大学1年生向けの解説

海の上を走る船をカメラでずっと追い続けるのは、波のしぶきで見えにくくなったり、船同士が重なったりするため、実はとても難しい技術です。この研究では、AIが船の動きを正しく学習できるように、たくさんの船の映像に正解ラベルを付けた「お手本データ」を新しく作りました。そして、既存の有名なAIたちにそのデータを使わせてみて、どれくらい正確に船を追いかけられるかをテストしました。これによって、将来の自動運転船や海の安全を守るシステムの開発がよりスムーズに進むようになります。
