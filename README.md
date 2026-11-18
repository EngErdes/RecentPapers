# SINDy支援型無香料カルマンフィルタを用いた、GNSS遮断下でのMEMS-IMU航法のための解釈可能なマルチソース融合

**Original Title**: *Interpretable Multi-Source Fusion for GNSS-Denied MEMS-IMU Navigation Using a SINDy-Aided Unscented Kalman Filter*

> **💡 一言要約**: SINDyで誤差を数式化し、GPSなしでも迷わない

| 項目 | 内容 |
|---|---|
| **著者** | Z Wang, K Feng, J Li, S Shen, Z Sun |
| **掲載誌** | IEEE Sensors Journal 2026 |
| **アラートキーワード** | kalman filter |
| **原文リンク** | [https://ieeexplore.ieee.org/abstract/document/11793976/](https://ieeexplore.ieee.org/abstract/document/11793976/) |
| **PDF版要約** | [README.pdf](./README.pdf) |

---

## 📊 新規性の図解（先行研究との違いと本研究のブレークスルー）

```mermaid
%%{init: {'flowchart': {'wrappingWidth': 520, 'nodeSpacing': 18, 'rankSpacing': 28, 'padding': 14, 'curve': 'basis'}, 'themeVariables': {'fontSize': '14px'}}}%%
flowchart TD
    S1["<b>【1. 先行研究の限界】 誤差累積とブラックボックス化</b><br/>──────────────────────────────<br/>GNSS遮断で誤差が急増し、AIによる補正は中身が不明で信頼性に欠けるという課題がある。"]
    S2["<b>【2. 本研究の着眼点】 誤差動態の数式化という発想</b><br/>──────────────────────────────<br/>複雑なセンサーのズレを、あえてシンプルな数式の組み合わせとして表現する点に着目した。"]
    S3["<b>【3. 技術的な新規性】 SINDyとUKFの高度な統合</b><br/>──────────────────────────────<br/>SINDyで導いた解釈可能な数式をUKFのアルゴリズムに組み込み、多源情報を融合させた。"]
    S4["<b>【4. 新規性による優位性】 透明性と高精度の両立</b><br/>──────────────────────────────<br/>数学的根拠に基づく補正により、GNSSがなくても長期間正確で信頼できる航法が可能になった。"]
    S1 --> S2
    S2 --> S3
    S3 --> S4
    style S1 fill:#EFF6FF,stroke:#1E40AF,stroke-width:2px,color:#111827,rx:8,ry:8
    style S2 fill:#F0FDFA,stroke:#0F766E,stroke-width:2px,color:#111827,rx:8,ry:8
    style S3 fill:#F5F3FF,stroke:#6D28D9,stroke-width:2px,color:#111827,rx:8,ry:8
    style S4 fill:#FFF7ED,stroke:#C2410C,stroke-width:2px,color:#111827,rx:8,ry:8
```

## 📝 要約

GNSSが利用できない環境において、MEMS-IMUの誤差が急速に蓄積する課題を解決するための新しい航法フレームワークです。SINDy（非線形動力学のスパース識別）を無香料カルマンフィルタ（UKF）に統合することで、誤差の挙動を数式として明示的にモデル化し、高精度で解釈可能な位置推定を実現しました。

## ❓ どんな問題に取り組んだか

GNSS信号が届かない場所では、安価なMEMS-IMUセンサーのみに頼ると誤差が指数関数的に増大し、正確な位置特定が困難になります。また、近年の深層学習を用いた補正手法は、なぜその結果になるのかという「解釈性」に乏しく、ミッションクリティカルな用途での信頼性に課題がありました。

## ✨ 何が新しい？何がすごい？（新規性）

物理的知見に基づいたデータ駆動手法であるSINDyを用いて、複雑なセンサー誤差の動態をスパースな数式として特定した点が最大の新規性です。これにより、ブラックボックスなAIモデルとは異なり、ナビゲーションの補正プロセスを人間が理解可能な形式で表現することに成功しました。この識別されたモデルをUKFの予測ステップに組み込むことで、非線形な環境下でも従来のフィルタリング手法を凌駕する推定精度と安定性を達成しています。

## 🎓 大学1年生向けの解説

トンネルや地下などGPSが使えない場所では、車やロボットは自分の動きを測るセンサー（IMU）だけで場所を計算しますが、これには少しずつズレが溜まる弱点があります。この研究では、そのズレが「どんな数式に従って起きるのか」を自動で見つけ出す魔法のような技術を使いました。計算の仕組みが数式として見えるので安心感があり、かつ非常に正確に自分の場所を予測し続けることができるようになりました。
