# 拡張カルマンフィルタを用いた慣性航法システムおよびINS/GPS統合における最適パラメータ推定

**Original Title**: *Optimal Parameter Estimation in Inertial Navigation Systems and INS/GPS Integration Using an Enhanced Kalman Filter*

> **💡 一言要約**: PID制御を融合し推定誤差を打破した新世代フィルタ

| 項目 | 内容 |
|---|---|
| **著者** | J Jamali, MHF Dindarloo, MA Rahgoshai, O Mahdiyar… |
| **アラートキーワード** | kalman filter |
| **PDF** | [https://amfad.sndu.ac.ir/article_4102_9ca8c9b0996bbf05ae7753d34667a6fd.pdf](https://amfad.sndu.ac.ir/article_4102_9ca8c9b0996bbf05ae7753d34667a6fd.pdf) |
| **原文リンク** | [https://amfad.sndu.ac.ir/article_4102_9ca8c9b0996bbf05ae7753d34667a6fd.pdf](https://amfad.sndu.ac.ir/article_4102_9ca8c9b0996bbf05ae7753d34667a6fd.pdf) |
| **PDF版要約** | [README.pdf](./README.pdf) |

---

## 📊 新規性の図解（先行研究との違いと本研究のブレークスルー）

```mermaid
%%{init: {'flowchart': {'wrappingWidth': 520, 'nodeSpacing': 18, 'rankSpacing': 28, 'padding': 14, 'curve': 'basis'}, 'themeVariables': {'fontSize': '14px'}}}%%
flowchart TD
    S1["<b>【1. 先行研究の限界】 従来手法の精度限界</b><br/>──────────────────────────────<br/>急激な変化や累積誤差の抑制が難しく、長時間の推定精度が低下していた。"]
    S2["<b>【2. 本研究の着眼点】 制御理論との融合</b><br/>──────────────────────────────<br/>推定器に制御工学のPIDの考え方を組み込むという、斬新な発想に注目した。"]
    S3["<b>【3. 技術的な新規性】 PID項の直接組み込み</b><br/>──────────────────────────────<br/>標準カルマンフィルタに積分・微分項を加え、誤差を動的に補正する構造を構築。"]
    S4["<b>【4. 新規性による優位性】 劇的なエラー削減</b><br/>──────────────────────────────<br/>積分項でズレを抑え、微分項で変化に即応する、安定した高精度推定を達成。"]
    S1 --> S2
    S2 --> S3
    S3 --> S4
    style S1 fill:#EFF6FF,stroke:#1E40AF,stroke-width:2px,color:#111827,rx:8,ry:8
    style S2 fill:#F0FDFA,stroke:#0F766E,stroke-width:2px,color:#111827,rx:8,ry:8
    style S3 fill:#F5F3FF,stroke:#6D28D9,stroke-width:2px,color:#111827,rx:8,ry:8
    style S4 fill:#FFF7ED,stroke:#C2410C,stroke-width:2px,color:#111827,rx:8,ry:8
```

## 📝 要約

慣性航法システム（INS）とGPSの統合精度を向上させるため、標準的なカルマンフィルタにPID制御の概念を組み込んだ新しい手法を提案しています。積分項と微分項をフィルタ構造に導入することで、従来の手法よりも推定誤差を大幅に削減することに成功しました。

## ❓ どんな問題に取り組んだか

従来のカルマンフィルタを用いたINS/GPS統合システムでは、センサーのノイズや動的な環境変化によって誤差が蓄積しやすいという課題がありました。特に、長時間の運用におけるドリフト誤差や急激な姿勢変化への追従性の不足が、精度の限界となっていました。

## ✨ 何が新しい？何がすごい？（新規性）

本研究の最大の特徴は、制御工学で定評のあるPID（比例・積分・微分）コントローラのアルゴリズムをカルマンフィルタの枠組みに統合した点にあります。積分項（I）により定常的な偏差を打ち消し、微分項（D）により急激な変動への応答性を高めることで、先行研究にはない強力な誤差補正能力を実現しました。このシンプルな枠組みにより、計算負荷を抑えつつ推定精度を飛躍的に高めています。

## 🎓 大学1年生向けの解説

ドローンや自動運転車が自分の場所を知るには、GPSと加速センサーなどを組み合わせて計算します。しかし、計算にはどうしても少しずつ誤差が混ざり、時間が経つと場所がズレてしまいます。この研究では、エアコンの温度調節などに使われる「PID制御」という賢い仕組みを、位置計算の数式に合体させました。その結果、急に動いても、時間が経ってもズレにくい、非常に正確な位置追計ができるようになりました。
