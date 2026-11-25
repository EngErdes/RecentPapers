# LiDAR、ROS 2、Raspberry Pi 5を用いた救助活動用地図作成ロボット

**Original Title**: *Map-Making Robot for Rescue Operations Using LiDAR, ROS 2 and Raspberry Pi 5*

> **💡 一言要約**: 最新ラズパイで救助用地図を正確に描く

| 項目 | 内容 |
|---|---|
| **著者** | NH Thet, PP Thu, VC Udegbu, A Bhattarai… |
| **掲載誌** | IEEE 14th Conference … 2026 |
| **アラートキーワード** | kalman filter |
| **原文リンク** | [https://ieeexplore.ieee.org/abstract/document/11791270/](https://ieeexplore.ieee.org/abstract/document/11791270/) |
| **PDF版要約** | [README.pdf](./README.pdf) |

---

## 📊 新規性の図解（先行研究との違いと本研究のブレークスルー）

```mermaid
%%{init: {'flowchart': {'wrappingWidth': 520, 'nodeSpacing': 18, 'rankSpacing': 28, 'padding': 14, 'curve': 'basis'}, 'themeVariables': {'fontSize': '14px'}}}%%
flowchart TD
    S1["<b>【1. 先行研究の限界】 低コストセンサーの限界</b><br/>──────────────────────────────<br/>安価なセンサーでは移動中の誤差が蓄積し、地図が大きく歪んでしまう問題があった。"]
    S2["<b>【2. 本研究の着眼点】 複数センサーの高度な融合</b><br/>──────────────────────────────<br/>エンコーダとIMUの利点を組み合わせ、互いの欠点を補い合う手法に着目した。"]
    S3["<b>【3. 技術的な新規性】 EKFとPi 5の活用</b><br/>──────────────────────────────<br/>高速なRaspberry Pi 5上で拡張カルマンフィルタを動かし、リアルタイムで位置を補正。"]
    S4["<b>【4. 新規性による優位性】 圧倒的な位置精度の向上</b><br/>──────────────────────────────<br/>旋回誤差を劇的に改善し、2.6cmという極めて高い移動精度を安価なシステムで実現した。"]
    S1 --> S2
    S2 --> S3
    S3 --> S4
    style S1 fill:#EFF6FF,stroke:#1E40AF,stroke-width:2px,color:#111827,rx:8,ry:8
    style S2 fill:#F0FDFA,stroke:#0F766E,stroke-width:2px,color:#111827,rx:8,ry:8
    style S3 fill:#F5F3FF,stroke:#6D28D9,stroke-width:2px,color:#111827,rx:8,ry:8
    style S4 fill:#FFF7ED,stroke:#C2410C,stroke-width:2px,color:#111827,rx:8,ry:8
```

## 📝 要約

最新のRaspberry Pi 5とROS 2を搭載し、救助活動を支援するための高精度な地図作成ロボットを開発しました。拡張カルマンフィルタ（EKF）を用いて車輪エンコーダとIMUのデータを融合し、自己位置推定の誤差を大幅に削減することに成功しています。

## ❓ どんな問題に取り組んだか

災害現場のような複雑な環境では、ロボットが自分の位置を正確に把握できず、作成される地図に大きなズレが生じることが課題でした。特に、安価なセンサーだけでは旋回時や移動時の誤差が蓄積しやすく、実用的な地図を作るのが困難でした。

## ✨ 何が新しい？何がすごい？（新規性）

最新のRaspberry Pi 5の高い処理能力を活かし、ROS 2環境下で高度なセンサー融合を実現しました。拡張カルマンフィルタ（EKF）により、エンコーダのオドメトリとIMUの角速度データを最適に統合し、方位角の誤差を従来手法から劇的に改善しています。具体的には、1.12mの移動に対して平均線形誤差2.6cm、方位角誤差3.6度という、低コストな構成ながら極めて高い精度を達成しました。

## 🎓 大学1年生向けの解説

災害現場などで人間の代わりに中を調べて地図を作ってくれるロボットの研究です。最新の小型コンピューター「Raspberry Pi 5」を頭脳として使い、レーザーで周りを測るセンサー（LiDAR）を搭載しています。タイヤが回った距離と、ロボットの向きを感じるセンサーの情報を数学的な工夫（EKF）で組み合わせることで、自分がどこにいるかを非常に正確に把握できるようになりました。これにより、複雑な場所でもズレの少ない正しい地図を自動で作ることができます。
