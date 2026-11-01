# Raqeeb：メガイベントにおける先端的セキュリティのためのプライバシー保護型AIビデオ解析

**Original Title**: *Raqeeb: Privacy-Preserving AI Video Analytics for Proactive Security at Mega-Events*

> **💡 一言要約**: 匿名化AIでイベントの安全とプライバシーを両立

| 項目 | 内容 |
|---|---|
| **著者** | Z Albalawi |
| **掲載誌** | 2026 |
| **アラートキーワード** | Multi Camera Tracking |
| **PDF** | [https://www.researchgate.net/profile/Ziad-Albalawi/publication/416882078_Raqeeb_Privacy-Preserving_AI_Video_Analytics_for_Proactive_Security_at_Mega-_Events/links/6adf40ad0fef1c1d0a0bedac/Raqeeb-Privacy-Preserving-AI-Video-Analytics-for-Proactive-Security-at-Mega-Events.pdf](https://www.researchgate.net/profile/Ziad-Albalawi/publication/416882078_Raqeeb_Privacy-Preserving_AI_Video_Analytics_for_Proactive_Security_at_Mega-_Events/links/6adf40ad0fef1c1d0a0bedac/Raqeeb-Privacy-Preserving-AI-Video-Analytics-for-Proactive-Security-at-Mega-Events.pdf) |
| **原文リンク** | [https://www.researchgate.net/profile/Ziad-Albalawi/publication/416882078_Raqeeb_Privacy-Preserving_AI_Video_Analytics_for_Proactive_Security_at_Mega-_Events/links/6adf40ad0fef1c1d0a0bedac/Raqeeb-Privacy-Preserving-AI-Video-Analytics-for-Proactive-Security-at-Mega-Events.pdf](https://www.researchgate.net/profile/Ziad-Albalawi/publication/416882078_Raqeeb_Privacy-Preserving_AI_Video_Analytics_for_Proactive_Security_at_Mega-_Events/links/6adf40ad0fef1c1d0a0bedac/Raqeeb-Privacy-Preserving-AI-Video-Analytics-for-Proactive-Security-at-Mega-Events.pdf) |
| **PDF版要約** | [README.pdf](./README.pdf) |

---

## 📊 新規性の図解（先行研究との違いと本研究のブレークスルー）

```mermaid
%%{init: {'flowchart': {'wrappingWidth': 520, 'nodeSpacing': 18, 'rankSpacing': 28, 'padding': 14, 'curve': 'basis'}, 'themeVariables': {'fontSize': '14px'}}}%%
flowchart TD
    S1["<b>【1. 先行研究の限界】 プライバシー侵害の懸念</b><br/>──────────────────────────────<br/>監視映像から個人の行動や特定が容易になり、プライバシーが脅かされる"]
    S2["<b>【2. 本研究の着眼点】 識別情報の完全な分離</b><br/>──────────────────────────────<br/>個人IDをカメラや場所と紐付かないランダムな記号に置き換える着想"]
    S3["<b>【3. 技術的な新規性】 SHA-256による仮名化</b><br/>──────────────────────────────<br/>ビデオのハッシュとIDを混ぜ、情報を漏らさない複雑な仮名に変換する"]
    S4["<b>【4. 新規性による優位性】 安全なイベント監視</b><br/>──────────────────────────────<br/>誰かを特定することなく不審な挙動のみを検出し、安全管理を実現する"]
    S1 --> S2
    S2 --> S3
    S3 --> S4
    style S1 fill:#EFF6FF,stroke:#1E40AF,stroke-width:2px,color:#111827,rx:8,ry:8
    style S2 fill:#F0FDFA,stroke:#0F766E,stroke-width:2px,color:#111827,rx:8,ry:8
    style S3 fill:#F5F3FF,stroke:#6D28D9,stroke-width:2px,color:#111827,rx:8,ry:8
    style S4 fill:#FFF7ED,stroke:#C2410C,stroke-width:2px,color:#111827,rx:8,ry:8
```

## 📝 要約

大規模イベントにおいて、個人のプライバシーを侵害することなくAIによる高度な監視を実現するシステム「Raqeeb」を提案しています。SHA-256ハッシュを活用して個人の追跡IDを匿名の仮名に変換し、場所や個人情報と紐付けない新しいデータ処理手法を導入しました。

## ❓ どんな問題に取り組んだか

大規模イベントでのセキュリティ監視は不可欠ですが、AIによるビデオ解析は個人の行動履歴やアイデンティティを暴くリスクがあり、プライバシー保護が課題でした。従来のシステムでは、カメラの設置場所や追跡データから、特定の個人が容易に割り出されてしまう危険性がありました。

## ✨ 何が新しい？何がすごい？（新規性）

ソースビデオのハッシュ値とトラッカーIDを組み合わせ、SHA-256を用いた「P-NNNN」形式の公開仮名へマッピングする独自のレジストリ手法を開発しました。この仮名はカメラ番号や位置情報を一切含まず、事後処理によって個人識別を完全に排除する構造を持っています。これにより、リアルタイムのセキュリティ監視と厳格なプライバシー保護を高い次元で両立させた点が画期的です。

## 🎓 大学1年生向けの解説

たくさんの人が集まるイベントで、怪しい動きをAIで自動的に見つけるシステムの研究です。ただし、映像をそのまま使うと誰がどこにいるかバレてしまうため、この研究では「名前」や「場所」を暗号のような記号に置き換える工夫をしました。AIには「誰か」はわからなくても「何かが起きている」ことだけが伝わるようにして、みんなのプライバシーを守りながら安全を保ちます。
