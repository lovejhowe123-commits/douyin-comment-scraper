"""
评论提取模块 - 进入视频页、滚动加载评论、文本清洗
"""
import re
import time
from typing import Optional

from playwright.sync_api import Page


# 页面底部干扰文本过滤
SKIP_WORDS = [
    "京ICP", "京公网", "广播电视",
    "精选", "推荐", "AI抖音", "关注", "朋友", "我的",
    "直播", "放映厅", "短剧", "小游戏",
    "充钻石", "客户端", "壁纸", "通知", "投稿", "搜索", "登录",
    "广告投放", "用户服务协议", "隐私政策", "账号找回", "联系我们",
    "加入我们", "营业执照", "友情链接", "站点地图", "下载抖音", "抖音电商",
    "网络谣言", "网上有害", "视频数据加载",
    "开启读屏", "读屏标签", "留言", "转发", "下载抖音精选",
    "推荐歌单", "全部歌单",
]


def scroll_for_comments(page: Page, scroll_times: int = 15, delay: float = 0.8):
    """滚动页面以触发评论加载"""
    for _ in range(scroll_times):
        page.evaluate("window.scrollBy(0, 400)")
        time.sleep(delay)
    time.sleep(2)


def extract_comments_from_page(page: Page) -> list[str]:
    """从页面文本中提取评论内容"""
    body = page.evaluate("document.body.innerText")
    lines = body.split("\n")

    # 过滤垃圾行
    filtered = []
    for l in lines:
        l = l.strip()
        if not l or len(l) < 4:
            continue
        if any(w in l for w in SKIP_WORDS):
            continue
        filtered.append(l)

    # 找到"全部评论"标记后的内容
    comments = []
    in_section = False

    for l in filtered:
        if "全部评论" in l:
            in_section = True
            continue
        if in_section:
            if "留下你的精彩评论吧" in l or "说点什么" in l:
                continue
            if "相关推荐" in l or "热门内容" in l or "为你推荐" in l:
                continue
            if any(s in l for s in ["精选", "推荐", "AI抖音", "关注", "朋友", "我的"]):
                continue
            comments.append(l)

    # 清洗——去掉元数据行
    clean = []
    for c in comments:
        c = c.strip()
        if re.match(r"^\d+[月天小时]前·\w+$", c):   continue
        if re.match(r"^\d+月前$", c):                  continue
        if re.match(r"^\d+天前$", c):                  continue
        if re.match(r"^\d+小时前$", c):                continue
        if re.match(r"^展开\d+条回复$", c):            continue
        if c == "回复":                                continue
        if re.match(r"^粉丝[\d.]+万?获赞[\d.]+万?$", c): continue
        if c == "作者回复过":                          continue
        if len(c) < 5:                                 continue
        clean.append(c)

    return clean


def get_video_meta(page: Page) -> dict:
    """从视频页面提取标题、作者信息"""
    meta = {"title": "", "author": ""}

    for sel in ["h1", '[class*="title"]', '[class*="desc"]', 'span[class*="title"]']:
        el = page.query_selector(sel)
        if el:
            try:
                t = el.inner_text().strip()
                if t:
                    meta["title"] = t
                    break
            except:
                pass

    for sel in ['[class*="author"]', '[class*="nickname"]', '[class*="name"]']:
        el = page.query_selector(sel)
        if el:
            try:
                a = el.inner_text().strip()
                if a:
                    meta["author"] = a
                    break
            except:
                pass

    return meta


def fetch_comments(
    page: Page,
    video_id: str,
    max_comments: int = 40,
) -> Optional[dict]:
    """
    进入视频页并提取评论

    Returns:
        {
            "video_id": str,
            "url": str,
            "title": str,
            "author": str,
            "comments": list[str],
            "total": int,
        }
    """
    url = f"https://www.douyin.com/video/{video_id}"
    page.goto(url, wait_until="domcontentloaded", timeout=25000)
    time.sleep(5)

    # 检测是否被跳转（反爬）
    actual_url = page.evaluate("window.location.href")
    if "/video/" not in actual_url:
        print(f"  ⚠️ 被跳转: {actual_url[:80]}，跳过")
        return None

    meta = get_video_meta(page)
    print(f"  标题: {meta['title'][:60] or 'N/A'}")
    print(f"  作者: {meta['author'] or 'N/A'}")

    # 滚动加载评论
    scroll_for_comments(page)

    # 提取
    comments = extract_comments_from_page(page)

    # 如果评论太少，加大滚动
    if len(comments) < 5:
        scroll_for_comments(page, scroll_times=10, delay=0.5)
        more = extract_comments_from_page(page)
        # 合并去重
        seen = set(comments)
        for c in more:
            if c not in seen:
                seen.add(c)
                comments.append(c)

    result = {
        "video_id": video_id,
        "url": url,
        "title": meta["title"],
        "author": meta["author"],
        "comments": comments[:max_comments],
        "total": min(len(comments), max_comments),
    }

    print(f"  💬 评论: {result['total']} 条")
    return result


# ===== 评论过滤工具 =====

AI_KEYWORDS = [
    "AI", "人工智能", "工具", "怎么", "如何", "哪里", "需要", "推荐", "求",
    "想做", "创业", "项目", "赚钱", "学习", "免费", "教程", "靠谱",
    "软件", "平台", "生成", "制作", "代码", "自动化", "有没有",
    "好做", "能做", "要钱", "怎么搞", "想做", "请问", "哪个", "求带",
    "适合", "小白", "新手", "零基础", "入门",
    "难", "坑", "有用吗", "试试", "值得", "哪款", "推荐个",
    "变现", "副业", "风口", "赛道", "普通人", "机会",
    "骗局", "割韭菜",
]


def filter_by_keywords(comments: list[str], keywords: list[str] = None) -> list[str]:
    """过滤包含指定关键词的评论"""
    if keywords is None:
        keywords = AI_KEYWORDS
    return [
        c for c in comments
        if any(k.lower() in c.lower() for k in keywords)
    ]


def keyword_frequency(comments: list[str], keywords: list[str] = None) -> dict[str, int]:
    """统计关键词在评论中出现的频率"""
    if keywords is None:
        keywords = AI_KEYWORDS
    text = " ".join(comments)
    return {kw: text.count(kw) for kw in keywords if text.count(kw) > 0}