#!/usr/bin/env python3
"""douyin-comment-scraper CLI 入口"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from .browser import create_browser, create_context, check_login, wait_for_login
from .search import search_videos
from .comments import fetch_comments, filter_by_keywords, get_video_meta
from .export import export_json, export_csv, export_markdown


def build_video_url(video_id: str) -> str:
    return f"https://www.douyin.com/video/{video_id}"


def run(args: argparse.Namespace):
    print(f"\n{'='*60}")
    print(f"  🎬 douyin-comment-scraper")
    print(f"  关键词: {args.keyword}")
    print(f"  视频数: {args.max_videos}  |  评论数/视频: {args.max_comments}")
    print(f"{'='*60}\n")

    browser = None
    try:
        browser = create_browser(headless=args.headless)
        context = create_context(browser, cookies_path=args.cookies)
        page = context.new_page()

        # 登录检测
        print(">> 检测登录状态...")
        logged_in = check_login(page)
        if not logged_in:
            if args.cookies:
                print("  ❌ Cookie 失效，请重新导出")
                sys.exit(1)
            if not args.headless:
                if not wait_for_login(page):
                    print("  ❌ 登录超时，退出")
                    sys.exit(1)
            else:
                print("  ❌ 未登录且 headless 模式无法扫码，请提供 Cookie 文件")
                sys.exit(1)
        else:
            print("  ✅ 已登录\n")

        # 搜索视频
        videos = search_videos(
            page,
            keyword=args.keyword,
            sort_type=args.sort,
            max_scroll=args.scroll,
        )

        if not videos:
            print("❌ 未找到视频")
            return

        print(f"\n>> 共找到 {len(videos)} 个视频，取前 {args.max_videos} 个提取评论\n")

        # 提取评论
        results = []
        for idx, v in enumerate(videos[: args.max_videos]):
            vid = v["id"]
            print(f"\n--- 视频 {idx+1}/{args.max_videos}: {vid} ---")
            print(f"    {v.get('author','?')}: {v.get('desc','')[:70]}")

            result = fetch_comments(page, vid, max_comments=args.max_comments)
            if result is None:
                continue

            # 补充视频搜索时获取的元信息
            result["author"] = result["author"] or v.get("author", "")
            result["digg_count"] = v.get("digg_count", "?")
            result["comment_count"] = v.get("comment_count", "?")

            # AI 相关评论过滤
            ai_c = filter_by_keywords(result["comments"])
            result["ai_comments"] = ai_c
            result["ai_count"] = len(ai_c)

            results.append(result)
            print(f"    🤖 AI相关评论: {len(ai_c)} 条")

        # 导出
        if not results:
            print("\n❌ 未成功获取任何视频的评论")
            return

        output_base = args.output or f"douyin_{args.keyword}_{time.strftime('%Y%m%d_%H%M')}"

        if args.format in ("all", "json"):
            export_json(results, f"{output_base}.json")
        if args.format in ("all", "csv"):
            export_csv(results, f"{output_base}.csv")
        if args.format in ("all", "md"):
            export_markdown(results, f"{output_base}.md", keyword=args.keyword)

        print(f"\n✅ 完成! 共 {len(results)} 个视频, {sum(r['total'] for r in results)} 条评论")

    finally:
        if browser:
            browser.close()


def main():
    parser = argparse.ArgumentParser(
        description="抖音评论区采集工具 - douyin-comment-scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 搜索 AI创业 视频并提取评论(有头模式,可扫码登录)
  douyin-scrape --keyword AI创业 --headless=false

  # 使用 Cookie 文件, 无头模式, 导出 CSV+MD
  douyin-scrape --keyword AI创业 --cookies cookies.json --format csv,md

  # 搜索最新视频, 提取前 5 个视频各 50 条评论
  douyin-scrape --keyword AI工具 --sort 2 --max-videos 5 --max-comments 50
        """,
    )

    parser.add_argument("--keyword", "-k", default="AI创业", help="搜索关键词")
    parser.add_argument("--cookies", "-c", default=None, help="抖音 Cookie JSON 文件路径")
    parser.add_argument("--max-videos", "-n", type=int, default=3, help="要分析的视频数量 (默认 3)")
    parser.add_argument("--max-comments", "-m", type=int, default=40, help="每个视频提取的评论数 (默认 40)")
    parser.add_argument("--sort", "-s", type=int, default=1, choices=[1, 2], help="排序: 1=综合 2=最新")
    parser.add_argument("--scroll", type=int, default=8, help="搜索结果页滚动次数 (默认 8)")
    parser.add_argument("--format", "-f", default="all", choices=["all", "json", "csv", "md", "json,csv,md"],
                        help="输出格式 (默认 all)")
    parser.add_argument("--output", "-o", default=None, help="输出文件路径前缀")
    parser.add_argument("--headless", default=True, action=argparse.BooleanOptionalAction,
                        help="无头模式 (默认 true, 首次使用建议 --no-headless)")

    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()