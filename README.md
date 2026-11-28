# クラス不均衡に対するハイブリッド・リサンプリング手法の比較評価

**Original Title**: *A Comparative Evaluation of Hybrid Resampling Techniques for Class Imbalance*

> **💡 一言要約**: 増量と掃除の同時実行で、不均衡データの壁を打破

| 項目 | 内容 |
|---|---|
| **著者** | P Rajarajeswari, PJ Suryaprabha, M Navina… |
| **掲載誌** | 10th International … 2026 |
| **アラートキーワード** | SMOTE |
| **原文リンク** | [https://ieeexplore.ieee.org/abstract/document/11790111/](https://ieeexplore.ieee.org/abstract/document/11790111/) |
| **PDF版要約** | [README.pdf](./README.pdf) |

---

## 📊 新規性の図解（先行研究との違いと本研究のブレークスルー）

```mermaid
%%{init: {'flowchart': {'wrappingWidth': 520, 'nodeSpacing': 18, 'rankSpacing': 28, 'padding': 14, 'curve': 'basis'}, 'themeVariables': {'fontSize': '14px'}}}%%
flowchart TD
    S1["<b>【1. 先行研究の限界】 単純な増量による弊害</b><br/>──────────────────────────────<br/>データを増やすだけでは境界にノイズが残り誤認の原因となる"]
    S2["<b>【2. 本研究の着眼点】 ハイブリッド化の採用</b><br/>──────────────────────────────<br/>オーバーサンプリングとアンダーサンプリングを最適に組み合わせる"]
    S3["<b>【3. 技術的な新規性】 動的なノイズ除去連携</b><br/>──────────────────────────────<br/>SMOTE後にENN等を用いて境界付近の紛らわしいデータを消去する"]
    S4["<b>【4. 新規性による優位性】 クリーンな学習を実現</b><br/>──────────────────────────────<br/>クラス間の重なりが減少し、少数派の識別の正確性が大幅に向上"]
    S1 --> S2
    S2 --> S3
    S3 --> S4
    style S1 fill:#EFF6FF,stroke:#1E40AF,stroke-width:2px,color:#111827,rx:8,ry:8
    style S2 fill:#F0FDFA,stroke:#0F766E,stroke-width:2px,color:#111827,rx:8,ry:8
    style S3 fill:#F5F3FF,stroke:#6D28D9,stroke-width:2px,color:#111827,rx:8,ry:8
    style S4 fill:#FFF7ED,stroke:#C2410C,stroke-width:2px,color:#111827,rx:8,ry:8
```

## 📝 要約

不均衡データに対する機械学習の精度を向上させるため、SMOTEとアンダーサンプリングを組み合わせたハイブリッド手法を比較評価しています。SMOTE-TomekやSMOTE-ENNといった手法が、少数派クラスの補完とノイズ除去を同時に行い、分類性能を改善することを示しています。

## ❓ どんな問題に取り組んだか

機械学習では、特定のクラスが極端に少ない「クラス不均衡」が学習を困難にします。単純なデータ増強ではクラス間の境界が曖昧になりやすく、モデルの予測精度が十分に上がらないという課題がありました。

## ✨ 何が新しい？何がすごい？（新規性）

本研究は、データの増強（SMOTE）とノイズ除去（Tomek Links/ENN）を統合したハイブリッド手法の優位性を定量的に明らかにしました。単にデータを増やすだけでなく、増強後に生じる不適切なサンプルを動的に削除することで、より鮮明な決定境界を構築できる点を実証しています。特にSMOTE-ENNが多様な評価指標において高いロバスト性を示すことを結論付けました。

## 🎓 大学1年生向けの解説

AIに「当たり」と「ハズレ」を教える際、ハズレが多すぎるとAIは手抜きをして全部ハズレと答えがちになります。この研究は、少ない方のデータを人工的に増やしつつ、紛らわしいデータを掃除する「セット技」を比較しました。料理で言えば、具材を増やすだけでなく、余分なアクを抜くことで味を整えるような手法です。これにより、データの偏りに負けない、賢いAIを作ることができます。
