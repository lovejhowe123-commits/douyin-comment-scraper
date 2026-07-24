"""
浏览器管理模块 - Playwright 初始化、Cookie 注入、登录检测
"""
import json
import time
from pathlib import Path
from typing import Optional

from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page


def normalize_cookies(raw_cookies: list[dict]) -> list[dict]:
    """标准化 Cookie 格式，处理 sameSite 兼容性问题"""
    valid = []
    for c in raw_cookies:
        if not c.get("name") or c.get("value") is None:
            continue
        ss = c.get("sameSite")
        if ss in ("no_restriction", "unspecified", None):
            c["sameSite"] = "None"
        elif ss == "lax":
            c["sameSite"] = "Lax"
        elif ss == "strict":
            c["sameSite"] = "Strict"
        else:
            c["sameSite"] = "None"
        valid.append(c)
    return valid


def load_cookies(path: str | Path) -> list[dict]:
    """从 JSON 文件加载 Cookie"""
    with open(path) as f:
        raw = json.load(f)
    return normalize_cookies(raw)


def create_browser(headless: bool = True) -> Browser:
    """创建 Playwright Chromium 浏览器实例"""
    p = sync_playwright().start()
    browser = p.chromium.launch(
        headless=headless,
        executable_path="/snap/bin/chromium",
        args=[
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-blink-features=AutomationControlled",
        ],
    )
    return browser


def create_context(
    browser: Browser,
    cookies_path: Optional[str | Path] = None,
) -> BrowserContext:
    """创建浏览器上下文，可选注入 Cookie"""
    context = browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        viewport={"width": 1920, "height": 1080},
        locale="zh-CN",
    )
    if cookies_path and Path(cookies_path).exists():
        cookies = load_cookies(cookies_path)
        context.add_cookies(cookies)
    return context


def check_login(page: Page) -> bool:
    """检测是否已登录抖音"""
    page.goto("https://www.douyin.com/", wait_until="domcontentloaded", timeout=20000)
    time.sleep(3)
    body_text = page.evaluate("document.body.innerText")[:500]
    if "登录" in body_text and "推荐" not in body_text:
        return False
    return True


def wait_for_login(page: Page, timeout: int = 120000) -> bool:
    """等待用户手动扫码登录"""
    print("⚠️ 请扫码登录抖音（你有 120 秒）...")
    try:
        page.wait_for_url(
            lambda url: "passport" not in url and "login" not in url,
            timeout=timeout,
        )
        print("✅ 登录成功")
        return True
    except:
        print("❌ 登录超时")
        return False