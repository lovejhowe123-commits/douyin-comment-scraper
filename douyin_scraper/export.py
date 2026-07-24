"""数据导出模块 - CSV / JSON / Markdown 报告生成"""
import csv
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from .comments import AI_KEYWORDS


def export_json(data: list[dict], output_path: str | Path):
    """导出 JSON 格式"""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  ✅ JSON: {output_path}")


def export_csv(data: list[dict], output_path: str | Path):
    """导出 CSV 格式（总览 + 评论明细）"""
    if not data:
        print("  ⚠️ 无数据，跳过 CSV 导出")
        return

    # 视频总览
    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["#", "作者", "标题", "链接", "评论数", "AI相关评论数"])
        for i, v in enumerate(data, 1):
            writer.writerow([
                i,
                v.get("author", ""),
                v.get("title", ""),
                v.get("url", ""),
                v.get("total", 0),
                len(v.get("ai_comments", [])),
            ])
    print(f"  ✅ CSV(总览): {output_path}")

    # 评论明细
    detail_path = output_path.replace(".csv", "_comments.csv")
    with open(detail_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["视频#", "作者", "评论内容", "是否AI相关"])
        for i, v in enumerate(data, 1):
            all_c = v.get("comments", [])
            ai_set = set(v.get("ai_comments", []))
            for c in all_c:
                writer.writerow([
                    i,
                    v.get("author", ""),
                    c,
                    "是" if c in ai_set else "",
                ])
    print(f"  ✅ CSV(明细): {detail_path}")


def export_markdown(
    data: list[dict],
    output_path: str | Path,
    keyword: str = "",
):
    """导出 Markdown 汇总报告"""
    all_text = []

    all_text.append(f"# 📊 抖音评论采集报告\n")
    all_text.append(f"**关键词**: {keyword or 'N/A'}")
    all_text.append(f"**采集时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    all_text.append(f"**视频数**: {len(data)}")
    all_text.append(f"---\n")

    # 每个视频
    all_comments_flat = []
    for i, v in enumerate(data):
        title = v.get("title") or "N/A"
        author = v.get("author") or "N/A"
        url = v.get("url", "")
        total = v.get("total", 0)
        ai_c = v.get("ai_comments", [])
        comments = v.get("comments", [])

        all_text.append(f"## 🔥 视频 {i+1}")
        all_text.append(f"- **标题**: {title}")
        all_text.append(f"- **作者**: {author}")
        all_text.append(f"- **评论数**: {total} | **AI相关**: {len(ai_c)}")
        all_text.append(f"- **链接**: {url}\n")

        if ai_c:
            all_text.append("### 🤖 AI相关评论")
            for c in ai_c[:10]:
                all_text.append(f"- {c}")
            all_text.append("")

        all_text.append("### 📝 全部评论")
        for j, c in enumerate(comments, 1):
            all_text.append(f"{j}. {c}")
        all_text.append("")

        all_comments_flat.extend(comments)

    # 词频统计
    all_text.append("## 📈 评论热词\n")
    text = " ".join(all_comments_flat)
    counts = {kw: text.count(kw) for kw in AI_KEYWORDS if text.count(kw) > 0}
    sorted_kw = sorted(counts.items(), key=lambda x: -x[1])[:20]
    all_text.append("| 关键词 | 频率 |")
    all_text.append("|--------|-----|")
    for kw, cnt in sorted_kw:
        all_text.append(f"| {kw} | {cnt} |")

    # 情绪分析（简单）
    pos_words = ["牛逼", "好用", "靠谱", "干货", "感谢", "收藏", "支持", "加油"]
    neg_words = ["骗", "割韭菜", "假", "没用", "坑", "智商税", "骗子", "垃圾"]
    pos = sum(text.count(w) for w in pos_words)
    neg = sum(text.count(w) for w in neg_words)
    sentiment = "🟢 偏正面" if pos > neg else ("🔴 偏负面" if neg > pos else "🟡 中性")

    all_text.append(f"\n## 💬 评论情绪\n")
    all_text.append(f"- **正面表达**: {pos} 处")
    all_text.append(f"- **负面表达**: {neg} 处")
    all_text.append(f"- **倾向**: {sentiment}")

    all_text.append(f"\n---\n*由 douyin-comment-scraper 自动生成 ({datetime.now().strftime('%Y-%m-%d %H:%M')})*")

    content = "\n".join(all_text)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✅ Markdown: {output_path}")

    # 控制台摘要
    print("\n" + "=" * 60)
    for i, v in enumerate(data):
        print(f"  #{i+1} {v.get('author','?')}: {v.get('title','')[:50]} "
              f"| 💬{v.get('total',0)} | 🤖{len(v.get('ai_comments',[]))}")
    print("=" * 60)