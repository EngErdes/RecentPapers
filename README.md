# Long-Term Optimal Delivery Planning for Replacing the Liqueﬁed Petroleum Gas Cylinder

| 項目 | 内容 |
|---|---|
| **PDF版要約** | [README.pdf](./README.pdf) |

---

## 📊 新規性の図解（先行研究との違いと本研究のブレークスルー）

```mermaid
%%{init: {'flowchart': {'wrappingWidth': 520, 'nodeSpacing': 18, 'rankSpacing': 28, 'padding': 14, 'curve': 'basis'}, 'themeVariables': {'fontSize': '14px'}}}%%
flowchart TD
    S1["<b>【4. 新規性による優位性】 主要な貢献・ブレークスルー</b><br/>──────────────────────────────<br/>The delivery route is obtained by solving two optimization problems sequentially. With the"]
    style S1 fill:#EFF6FF,stroke:#1E40AF,stroke-width:2px,color:#111827,rx:8,ry:8
```

## 📝 要約

The delivery route is obtained by solving two optimization problems sequentially. With
the ﬁrst problem, we determine a delivery route that maximizes the number of deliveries to
moderate-risk customers, ensuring deliveries to high-risk customers. When the two routes
have the same number of deliveries, the routes can diﬀer in terms of the working time.
Therefore, a second optimization problem is prepared to minimize the working time, ensuring
the replacement to the customers obtained from the ﬁrst optimization problem. When the
solution is not found within the time limit, the heuristic algorithms shown in Section 5.3 are
applied to determine the delivery route for applying the proposed system to the real world.

2-opt

混合整数計画問題を解くためのソルバーを使ったよ。

評価指標は

The quality of the replacement plan was investigated using the following evaluation metrics.
• Average traveling time per day (travel-time/day)
• Average traveling time per customer (travel-time/customer)
• Total number of nonreplacement visits (nonreplacement)
