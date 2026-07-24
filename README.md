# 🎬 douyin-comment-scraper

抖音评论区采集工具。搜索关键词视频 → 自动提取评论 → 导出结构化报告（JSON/CSV/Markdown）。

---

## 快速开始

```bash
# 1. 安装
pip install douyin-comment-scraper

# 2. 安装 Playwright 浏览器
playwright install chromium

# 3. 运行（首次建议有头模式，扫码登录）
douyin-scrape --keyword AI创业 --no-headless

# 4. 后续可用 Cookie 免登录
douyin-scrape --keyword AI创业 --cookies douyin_cookies.json
```

## 使用示例

```bash
# 搜索 AI 工具，提取前5个视频，各50条评论 → CSV + Markdown
douyin-scrape -k "AI工具" -n 5 -m 50 -f csv,md

# 搜索最新发布的 AI 创业视频
douyin-scrape -k "AI创业" -s 2 --cookies cookies.json

# 指定输出文件名
douyin-scrape -k "AI创业" -o my_report --cookies cookies.json
```

### 参数说明

| 参数 | 简写 | 默认值 | 说明 |
|------|------|--------|------|
| `--keyword` | `-k` | `AI创业` | 搜索关键词 |
| `--cookies` | `-c` | 无 | 抖音 Cookie JSON 文件路径 |
| `--max-videos` | `-n` | `3` | 要分析的视频数量 |
| `--max-comments` | `-m` | `40` | 每个视频提取的评论数 |
| `--sort` | `-s` | `1` | 排序：`1`=综合 `2`=最新 |
| `--format` | `-f` | `all` | 输出格式：`all`, `json`, `csv`, `md` |
| `--output` | `-o` | 自动生成 | 输出文件前缀 |
| `--no-headless` | | `True` | 有头模式（首次使用建议开启） |

## 前置条件

1. **Python ≥ 3.10**
2. **Chromium 浏览器** — `playwright install chromium`
3. **抖音登录状态**（两种方式）：
   - **A. Cookie 文件**：浏览器装 [Cookie-Editor](https://chromewebstore.google.com/detail/cookie-editor/hlffaajledmlnilfkjmmmkggbjpcckgo) → 登录抖音 → 导出 JSON → 传给 `--cookies`
   - **B. 有头模式扫码**：首次用 `--no-headless`，浏览器弹出后扫码登录

## 输出文件

运行后生成（以 `--format` 决定）：

- `douyin_关键词_日期时间.json` — 完整结构化数据
- `douyin_关键词_日期时间.csv` — 视频总览表
- `douyin_关键词_日期时间_comments.csv` — 评论明细表
- `douyin_关键词_日期时间.md` — 可视化报告（含词频、情绪分析）

## 注意事项

⚠️ **抖音反爬较强，不能保证永久可用。** 已知限制：

- Cookie 有效期约 1-7 天，过期需重新导出
- 抖音可能检测 headless 浏览器并跳转
- DOM 选择器可能随改版变化，需要时更新选择器
- 单个视频评论数过多时可能只加载部分（受滚动条限制）

## 项目结构

```
douyin-comment-scraper/
├── pyproject.toml          # 包配置
├── README.md               # 本文档
└── douyin_scraper/
    ├── __init__.py          # 版本
    ├── cli.py               # 命令行入口
    ├── browser.py           # 浏览器管理 + Cookie 注入
    ├── search.py            # 搜索视频 + API 拦截
    ├── comments.py          # 评论提取 + 清洗 + 关键词过滤
    └── export.py            # JSON/CSV/MD 导出
```

## License

MIT