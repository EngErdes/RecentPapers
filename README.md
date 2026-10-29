# Mining with Rarity: A Unifying Framework

| 項目 | 内容 |
|---|---|
| **PDF版要約** | [README.pdf](./README.pdf) |

---

## 📊 新規性の図解（先行研究との違いと本研究のブレークスルー）

```mermaid
%%{init: {'flowchart': {'wrappingWidth': 520, 'nodeSpacing': 18, 'rankSpacing': 28, 'padding': 14, 'curve': 'basis'}, 'themeVariables': {'fontSize': '14px'}}}%%
flowchart TD
    S1["<b>【4. 新規性による優位性】 主要な貢献・ブレークスルー</b><br/>──────────────────────────────<br/>引用元論文 : 稀なデータに関する関心 : 稀なクラス(不均衡データ) 稀なケース rare classと rare case の説明 Aが少数派class Bが多"]
    style S1 fill:#EFF6FF,stroke:#1E40AF,stroke-width:2px,color:#111827,rx:8,ry:8
```

## 📝 要約

引用元論文 :

稀なデータに関する関心 :

稀なクラス(不均衡データ)

稀なケース

rare classと

rare case

の説明

Aが少数派class

Bが多数派class

B2とかは多数派classの中の希少例

正解率 : 少数データに対してはうまく機能しない。

この結果（26のデータセットで平均）は、少数派クラスの分類ルールの誤分類率が、多数派クラスの事例を識別するルールの誤分類率の2〜3倍であることを示しており、また、同様に重要な点として、少数派クラスの事例は多数派クラスの事例よりも予測される可能性がはるかに低いことを示しています。情報検索の専門用語を使用すると、少数派クラスは多数派クラスよりもはるかに低い適合率（Precision）と再現率（Recall）を持ちます。多くの実務家が、クラス分布が極端に偏っている場合、少数派クラスの再現率がしばしば0になる、つまり少数派クラスに対して分類ルールが一切生成されない、という現象を観察しています。
