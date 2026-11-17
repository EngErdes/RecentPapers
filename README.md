# LLMのKVキャッシュ圧縮における高スループットなバイナリ類似度検索に向けた、デュアルチャネル共有OFA-p-SOT-MRAM CIMマクロ

**Original Title**: *Dual-channel-shared OFA-p-SOT-MRAM CIM Macro for High-throughput Binary Similarity Search in LLM KV-Cache Compression*

> **💡 一言要約**: メモリ内でLLMの高速検索を可能にする新型MRAM

| 項目 | 内容 |
|---|---|
| **著者** | F Gao, C Xiao, D Jiang, X Tang, J Zhao, T Yang, J Tang… |
| **掲載誌** | IEEE 8th International … 2026 |
| **アラートキーワード** | one shot |
| **原文リンク** | [https://ieeexplore.ieee.org/abstract/document/11761794/](https://ieeexplore.ieee.org/abstract/document/11761794/) |
| **PDF版要約** | [README.pdf](./README.pdf) |

---

## 📊 新規性の図解（先行研究との違いと本研究のブレークスルー）

```mermaid
%%{init: {'flowchart': {'wrappingWidth': 520, 'nodeSpacing': 18, 'rankSpacing': 28, 'padding': 14, 'curve': 'basis'}, 'themeVariables': {'fontSize': '14px'}}}%%
flowchart TD
    S1["<b>【1. 先行研究の限界】 外部磁場生成と低速な並列書き込み</b><br/>──────────────────────────────<br/>SOT-MRAMの制御に複雑な回路が必要で、一括書き込みも困難だった。"]
    S2["<b>【2. 本研究の着眼点】 既存回路の再利用と共有構造</b><br/>──────────────────────────────<br/>読み出し線を磁場生成に使い、データ線を共有して並列性を高める着想。"]
    S3["<b>【3. 技術的な新規性】 OFA方式とデュアルチャネル共有回路</b><br/>──────────────────────────────<br/>ビット線を流用した磁気制御と、行列同時書き込みを可能にする新設計。"]
    S4["<b>【4. 新規性による優位性】 高速検索とLLMメモリ負荷の低減</b><br/>──────────────────────────────<br/>高スループットな類似度検索により、LLMの動作を大幅に高速化した。"]
    S1 --> S2
    S2 --> S3
    S3 --> S4
    style S1 fill:#EFF6FF,stroke:#1E40AF,stroke-width:2px,color:#111827,rx:8,ry:8
    style S2 fill:#F0FDFA,stroke:#0F766E,stroke-width:2px,color:#111827,rx:8,ry:8
    style S3 fill:#F5F3FF,stroke:#6D28D9,stroke-width:2px,color:#111827,rx:8,ry:8
    style S4 fill:#FFF7ED,stroke:#C2410C,stroke-width:2px,color:#111827,rx:8,ry:8
```

## 📝 要約

大規模言語モデル（LLM）のKVキャッシュ圧縮を効率化するため、SOT-MRAMを用いたメモリ内演算（CIM）技術を提案しています。読み出しビット線を再利用して書き込みを制御するOFA方式と、行・列の並列書き込みを可能にする共有チャネル構造により、高速なバイナリ類似度検索を実現します。

## ❓ どんな問題に取り組んだか

LLMの実行には膨大なKVキャッシュが必要でメモリを圧迫しますが、その圧縮に必要な類似度検索は従来の演算では遅延が大きく、電力消費も激しいという課題があります。また、既存のMRAMは書き込みの制御や並列処理に制限がありました。

## ✨ 何が新しい？何がすごい？（新規性）

読み出しビット線を外部磁場生成に転用するOFA（Offset-Field-Assisted）方式を採用し、垂直磁気異方性を持つSOT-MRAMの確実な反転制御を低コストで実現しました。さらに、デュアルチャネル共有構造により、一度に複数箇所の書き込みが可能な「ワンショット並列書き込み」を達成しています。これにより、LLMの圧縮に必要なハッシュ値比較などの類似度検索をメモリ内で超高速に行えるようになりました。

## 🎓 大学1年生向けの解説

AI（ChatGPTなど）が長い文章を扱うとき、過去の情報を「KVキャッシュ」としてメモリに保存しますが、これが多すぎてコンピュータがパンクしてしまいます。この研究では、その情報をコンパクトにまとめる作業を、メモリの中で直接やってしまう新しいタイプのチップ（MRAM）を開発しました。読み出し回路を書き込み補助に使い回す賢い仕組みで、データの検索スピードを劇的に高めています。
