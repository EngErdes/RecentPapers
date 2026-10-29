# Mixed Effects Neural Networks (MeNets) with Applications to Gaze Estimation

| 項目 | 内容 |
|---|---|
| **PDF版要約** | [README.pdf](./README.pdf) |

---

## 📊 新規性の図解（先行研究との違いと本研究のブレークスルー）

```mermaid
%%{init: {'flowchart': {'wrappingWidth': 520, 'nodeSpacing': 18, 'rankSpacing': 28, 'padding': 14, 'curve': 'basis'}, 'themeVariables': {'fontSize': '14px'}}}%%
flowchart TD
    S1["<b>【4. 新規性による優位性】 主要な貢献・ブレークスルー</b><br/>──────────────────────────────<br/>視線推定 心理学や神経科学への応用でも重要 高い精度を維持するにはコストが必要 視線推定のタスクの捉え方 x \in \mathbb{R}^p \rightarrow y"]
    style S1 fill:#EFF6FF,stroke:#1E40AF,stroke-width:2px,color:#111827,rx:8,ry:8
```

## 📝 要約

視線推定

心理学や神経科学への応用でも重要

高い精度を維持するにはコストが必要

視線推定のタスクの捉え方

x \in \mathbb{R}^p \rightarrow y \in \mathbb{R}^3

統計的な仮定が満たされているかどうかを確認するのは、精度向上の自然なステップだ。

(A)The Eyediap dataset
