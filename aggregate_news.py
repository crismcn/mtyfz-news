from __future__ import annotations

import datetime
import html
import json
import os
import re
import time
from pathlib import Path
from typing import Any

import feedparser
import pytz
import requests


# ================= 配置 =================

RSS_URL = "https://news.google.com/rss/headlines/section/topic/WORLD?hl=en-US&gl=US&ceid=US:en"

REQUEST_TIMEOUT = 30
MAX_NEWS_ITEMS = 36
MIN_NEWS_ITEMS = 10

ASSET_ROOT = Path("assets") / "generated"

TIMEZONE = pytz.timezone("Asia/Shanghai")

MODELSCOPE_API_KEY = os.environ.get("MODELSCOPE_API_KEY") or "ms-86779415-739f-4ae7-bf39-3c0b89167aba"
MODELSCOPE_URL = "https://api-inference.modelscope.cn/v1/infer"
MODEL_ID = "ZhipuAI/GLM-4.7-Flash"

CHINA_RELATED_PATTERNS = [
    r"\bchina\b",
    r"\bchinese\b",
    r"\bbeijing\b",
    r"\bshanghai\b",
    r"\bhong kong\b",
    r"\bmacau\b",
    r"\bxi jinping\b",
    r"\btaiwan\b",
]


# ================= 工具函数 =================


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def is_china_related(text: str) -> bool:
    text = text.lower()
    return any(re.search(p, text) for p in CHINA_RELATED_PATTERNS)


# ================= RSS抓取 =================


def fetch_feed():
    resp = requests.get(
        RSS_URL,
        timeout=REQUEST_TIMEOUT,
        headers={"User-Agent": "daily-news-bot"},
    )
    resp.raise_for_status()

    return feedparser.parse(resp.content)


def collect_news_items(feed) -> list[dict]:
    items = []

    for entry in feed.entries:

        title = normalize(entry.get("title", ""))
        summary = normalize(re.sub(r"<[^>]+>", " ", entry.get("summary", "")))
        url = entry.get("link", "")

        text = f"{title} {summary}"

        if not title or is_china_related(text):
            continue

        items.append(
            {
                "index": len(items) + 1,
                "title": title,
                "summary": summary[:240],
                "url": url,
            }
        )

        if len(items) >= MAX_NEWS_ITEMS:
            break

    if len(items) < MIN_NEWS_ITEMS:
        raise RuntimeError("新闻数量过少")

    return items


# ================= AI调用 =================


def call_glm(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {MODELSCOPE_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODEL_ID,
        "input": prompt,
        "parameters": {"temperature": 0.4, "max_output_tokens": 1024},
    }

    r = requests.post(MODELSCOPE_URL, headers=headers, json=payload, timeout=REQUEST_TIMEOUT)
    r.raise_for_status()

    result = r.json()

    return result.get("output", "")


# ================= JSON解析 =================


def parse_json(text: str) -> dict:

    if not text:
        raise RuntimeError("AI返回为空")

    cleaned = text.strip()

    cleaned = re.sub(r"```json", "", cleaned)
    cleaned = re.sub(r"```", "", cleaned)

    match = re.search(r"\{.*\}", cleaned, re.S)

    if match:
        cleaned = match.group(0)

    return json.loads(cleaned)


# ================= Prompt =================


def build_prompt(item: dict) -> str:
    return f"""
你是国际新闻翻译助手。

任务：
把英文新闻翻译为简体中文。

要求：
必须只返回JSON。
不要markdown。
不要解释。

JSON格式：

{{
"title_cn":"中文标题",
"summary_cn":"中文摘要"
}}

新闻标题：
{item['title']}

新闻摘要：
{item['summary']}
"""


# ================= 翻译 =================


def translate_news(news_items: list[dict]) -> list[dict]:

    results = []

    for item in news_items:

        prompt = build_prompt(item)

        try:

            raw = call_glm(prompt)

            data = parse_json(raw)

            title_cn = normalize(data.get("title_cn", ""))
            summary_cn = normalize(data.get("summary_cn", ""))

            if not title_cn or not summary_cn:
                raise RuntimeError("AI字段缺失")

        except Exception as e:

            print("AI翻译失败，使用fallback:", e)

            title_cn = item["title"]
            summary_cn = item["summary"]

        results.append(
            {
                "title_cn": title_cn,
                "summary_cn": summary_cn,
                "url": item["url"],
            }
        )

        time.sleep(0.6)  # 防止限流

    return results


# ================= HTML =================


def render_html(news):

    date = datetime.datetime.now(TIMEZONE).strftime("%Y-%m-%d")

    parts = [
        "<html>",
        "<meta charset='utf-8'>",
        f"<h1>国际新闻日报 {date}</h1>",
    ]

    for n in news:

        parts.append(f"<h2>{html.escape(n['title_cn'])}</h2>")
        parts.append(f"<p>{html.escape(n['summary_cn'])}</p>")
        parts.append(f"<p><a href='{n['url']}'>原文链接</a></p>")
        parts.append("<hr>")

    parts.append("</html>")

    return "\n".join(parts)


# ================= Markdown =================


def render_md(news):

    date = datetime.datetime.now(TIMEZONE).strftime("%Y-%m-%d")

    parts = [f"# 国际新闻日报 {date}"]

    for n in news:
        parts.append(f"## {n['title_cn']}")
        parts.append(n["summary_cn"])
        parts.append(f"[原文链接]({n['url']})")
        parts.append("---")

    return "\n".join(parts)


# ================= 保存 =================


def save_outputs(html_content, md_content):

    ASSET_ROOT.mkdir(parents=True, exist_ok=True)

    html_file = ASSET_ROOT / "daily_news.html"
    md_file = ASSET_ROOT / "daily_news.md"

    html_file.write_text(html_content, encoding="utf-8")
    md_file.write_text(md_content, encoding="utf-8")

    print("输出完成：")
    print(html_file)
    print(md_file)


# ================= main =================


def main():

    print("抓取RSS...")

    feed = fetch_feed()

    news_items = collect_news_items(feed)

    print("新闻数量:", len(news_items))

    print("开始AI翻译...")

    translated = translate_news(news_items)

    html_content = render_html(translated)
    md_content = render_md(translated)

    save_outputs(html_content, md_content)


if __name__ == "__main__":
    main()
