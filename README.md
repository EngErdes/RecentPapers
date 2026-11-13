# YOLOv5とカルマンフィルタを用いたCCTV映像における移動方向分析機能付き車両追跡システムの最適化

**Original Title**: *OPTIMIZATION OF A YOLOV5 AND KALMAN FILTER-BASED VEHICLE TRACKING SYSTEM WITH VEHICLE MOVEMENT DIRECTION ANALYSIS IN CCTV VIDEO*

> **💡 一言要約**: 最新AIと予測技術で車両の動きを逃さず追跡

| 項目 | 内容 |
|---|---|
| **著者** | S Sumarno, FN Tambunan, PAMZR ZER |
| **掲載誌** | JURTEKSI (jurnal Teknologi dan Sistem … 2026 |
| **アラートキーワード** | kalman filter |
| **PDF** | [https://jurnal.stmikroyal.ac.id/index.php/jurteksi/article/download/4775/2339](https://jurnal.stmikroyal.ac.id/index.php/jurteksi/article/download/4775/2339) |
| **原文リンク** | [https://jurnal.stmikroyal.ac.id/index.php/jurteksi/article/download/4775/2339](https://jurnal.stmikroyal.ac.id/index.php/jurteksi/article/download/4775/2339) |
| **PDF版要約** | [README.pdf](./README.pdf) |

---

## 📊 新規性の図解（先行研究との違いと本研究のブレークスルー）

```mermaid
%%{init: {'flowchart': {'wrappingWidth': 520, 'nodeSpacing': 18, 'rankSpacing': 28, 'padding': 14, 'curve': 'basis'}, 'themeVariables': {'fontSize': '14px'}}}%%
flowchart TD
    S1["<b>【1. 先行研究の限界】 追跡の途切れと方向把握の困難</b><br/>──────────────────────────────<br/>車両の重なりに弱く、追跡が頻繁に途切れるほか、進行方向の正確な把握が困難だった。"]
    S2["<b>【2. 本研究の着眼点】 検出と予測の高度な融合</b><br/>──────────────────────────────<br/>高速なAI（YOLOv5）と予測モデルを組み合わせ、移動パターンの解析を統合した。"]
    S3["<b>【3. 技術的な新規性】 方向分析を加えた統合モデル</b><br/>──────────────────────────────<br/>カルマンフィルタで軌跡を補完しつつ、物体の移動ベクトルから進行方向を自動で特定。"]
    S4["<b>【4. 新規性による優位性】 複雑な交通下での安定追跡</b><br/>──────────────────────────────<br/>遮蔽があっても追跡を維持し、進行方向に基づいた精度の高い交通モニタリングを実現。"]
    S1 --> S2
    S2 --> S3
    S3 --> S4
    style S1 fill:#EFF6FF,stroke:#1E40AF,stroke-width:2px,color:#111827,rx:8,ry:8
    style S2 fill:#F0FDFA,stroke:#0F766E,stroke-width:2px,color:#111827,rx:8,ry:8
    style S3 fill:#F5F3FF,stroke:#6D28D9,stroke-width:2px,color:#111827,rx:8,ry:8
    style S4 fill:#FFF7ED,stroke:#C2410C,stroke-width:2px,color:#111827,rx:8,ry:8
```

## 📝 要約

物体検出アルゴリズムのYOLOv5と軌跡予測を行うカルマンフィルタを統合し、CCTV映像内の車両追跡と移動方向の解析を最適化した研究です。検出精度を維持しながら、カルマンフィルタによって車両の動きを予測することで、複雑な交通状況下でも安定したリアルタイム監視を実現しました。

## ❓ どんな問題に取り組んだか

都市部の監視カメラ（CCTV）映像において、車両同士の重なりや高速移動によって追跡が途切れてしまうことが大きな課題でした。また、単なる位置の把握だけでなく、車両がどの方向に進んでいるかを自動で正確に判別する仕組みが不足していました。

## ✨ 何が新しい？何がすごい？（新規性）

本研究は、高速な物体検出を実現するYOLOv5と、動体の軌跡を予測するカルマンフィルタを統合し、さらに「移動方向の自動分析」を組み込んだ点が独創的です。先行研究と比較して、検出後の軌跡の連続性を維持するアルゴリズムを最適化し、遮蔽物があっても追跡を継続できる仕組みを構築しました。これにより、交通違反の検知や高度な交通流解析が可能になるという具体的な貢献をしています。

## 🎓 大学1年生向けの解説

街中にある監視カメラの映像から、AIを使って「車」を自動で見つけ、追いかける技術についての研究です。最新のAIで車を見つけるだけでなく、数学的な方法（カルマンフィルタ）を使って「車が次にどこへ動くか」を予測するのがポイントです。これにより、車が他の車に隠れてしまっても見失わずに追い続けることができます。さらに、その車がどこに向かっているかも自動でわかるようになります。
