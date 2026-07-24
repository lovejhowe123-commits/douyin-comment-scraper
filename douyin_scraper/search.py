"""
视频搜索模块 - 搜索关键词、拦截 API 响应、提取视频列表
"""
import json
import time
from typing import Callable

from playwright.sync_api import Page


def extract_videos_from_api(body: str) -> list[dict]:
    """从搜索 API 响应中提取视频信息"""
    videos = []
    try:
        d = json.loads(body)
    except:
        try:
            d = json.loads(body.split("\r\n", 1)[-1].strip())
        except:
            return videos

    if not isinstance(d, dict):
        return videos

    data_arr = d.get("data")
    if isinstance(data_arr, list):
        for item in data_arr:
            if not isinstance(item, dict):
                continue
            aweme = item.get("aweme_info") or item.get("aweme_detail") or item
            if not isinstance(aweme, dict) or not aweme.get("aweme_id"):
                continue

            author_info = aweme.get("author", {})
            stats = aweme.get("statistics", {})
            videos.append(
                {
                    "id": aweme["aweme_id"],
                    "desc": (aweme.get("desc") or "")[:200],
                    "author": (
                        author_info.get("nickname", "?")
                        if isinstance(author_info, dict)
                        else "?"
                    ),
                    "digg_count": (
                        stats.get("digg_count", "?")
                        if isinstance(stats, dict)
                        else "?"
                    ),
                    "comment_count": (
                        stats.get("comment_count", "?")
                        if isinstance(stats, dict)
                        else "?"
                    ),
                    "create_time": aweme.get("create_time", 0),
                }
            )
    return videos


def setup_search_interceptor(page: Page, collector: list) -> Callable:
    """设置搜索 API 响应拦截器"""
    def handler(response):
        url = response.url
        if "/general/search/stream/" in url or "/general/search/single/" in url:
            try:
                vids = extract_videos_from_api(response.text())
                for v in vids:
                    if v not in collector:
                        collector.append(v)
            except:
                pass
    page.on("response", handler)
    return handler


def search_videos(
    page: Page,
    keyword: str,
    sort_type: int = 1,
    max_scroll: int = 8,
) -> list[dict]:
    """
    搜索视频并返回结果列表
    
    Args:
        page: Playwright 页面对象
        keyword: 搜索关键词
        sort_type: 1=综合排序, 2=最新发布
        max_scroll: 滚动加载次数
    
    Returns:
        视频列表，每个包含 id, desc, author, digg_count, comment_count
    """
    collector = []
    setup_search_interceptor(page, collector)

    encoded = keyword
    from urllib.parse import quote
    encoded = quote(keyword)

    url = f"https://www.douyin.com/search/{encoded}?type=general&sort_type={sort_type}"
    print(f"🔍 搜索: {keyword} (sort_type={sort_type})")
    page.goto(url, wait_until="domcontentloaded", timeout=20000)
    time.sleep(4)

    for _ in range(max_scroll):
        page.evaluate("window.scrollBy(0, 600)")
        time.sleep(1)
    time.sleep(2)

    # 去重
    seen = set()
    unique = []
    for v in collector:
        if v["id"] not in seen:
            seen.add(v["id"])
            unique.append(v)

    print(f"  找到 {len(unique)} 个视频")
    return unique