"""工具定义模块"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from langchain_core.tools import tool

from chathexo.settings import settings


def load_blog_index() -> Dict[str, Any]:
    """加载博客索引文件"""
    # 索引文件在项目根目录
    index_path = Path(__file__).parent.parent / settings.index_path
    with open(index_path, "r", encoding="utf-8") as f:
        return json.load(f)


@tool
def grep_tool(keywords: str) -> str:
    """
    在博客中搜索包含特定关键词的内容。适用于精确查找某个词或短语。
    支持多关键词OR搜索：只要文章包含任意一个关键词就会返回。

    重要：为了扩大搜索范围，建议提供5-10个相关关键词，用逗号或空格分隔。
    例如："新疆,阿勒泰,喀纳斯,禾木,旅行" 或 "Python 编程 代码 开发 教程"

    Args:
        keywords: 要搜索的关键词，多个关键词用逗号或空格分隔

    Returns:
        包含任意关键词的文章列表
    """
    data = load_blog_index()
    posts = data.get("posts", [])

    # 解析关键词：支持逗号或空格分隔
    keyword_list = []
    if "," in keywords:
        keyword_list = [k.strip().lower() for k in keywords.split(",") if k.strip()]
    else:
        keyword_list = [k.strip().lower() for k in keywords.split() if k.strip()]

    if not keyword_list:
        return "请提供至少一个关键词"

    hits = []
    for post in posts:  # 搜索所有文章
        content = post.get("content") or post.get("raw") or ""
        content_lower = content.lower()

        # OR 搜索：只要包含任意一个关键词就匹配
        if any(kw in content_lower for kw in keyword_list):
            title = post.get("title", "")
            url = post.get("url", "")
            hits.append(f"- {title}: {url}")

    if hits:
        return "\n".join(hits)
    else:
        return f"没有找到包含这些关键词的文章: {', '.join(keyword_list)}"


@tool
def list_recent_posts(count: int = 5) -> str:
    """
    列出最近更新的博客文章。

    Args:
        count: 要列出的文章数量，默认5篇

    Returns:
        最近更新的文章列表
    """
    data = load_blog_index()
    posts = data.get("posts", [])

    sorted_posts = sorted(
        posts,
        key=lambda p: p.get("updated") or p.get("date") or "",
        reverse=True,
    )[:count]

    results = []
    for i, post in enumerate(sorted_posts, 1):
        title = post.get("title", "")
        date = post.get("updated") or post.get("date") or ""
        url = post.get("url", "")
        results.append(f"{i}. {title}\n   更新时间: {date}\n   链接: {url}")

    return "\n\n".join(results)


@tool
def list_all_posts() -> str:
    """
    列出所有博客文章的标题和路径。

    Returns:
        所有文章的列表
    """
    data = load_blog_index()
    posts = data.get("posts", [])

    results = []
    for post in posts:
        title = post.get("title", "")
        path = post.get("path", "")
        results.append(f"- {title} ({path})")

    return "\n".join(results) if results else "没有找到文章"


@tool
def get_post_content(title_or_path: str) -> str:
    """
    获取指定文章的完整内容。

    Args:
        title_or_path: 文章标题或路径

    Returns:
        文章的内容
    """
    data = load_blog_index()
    posts = data.get("posts", [])

    post = None
    search_term = title_or_path.strip().lstrip("/")  # 去掉前导斜杠

    for p in posts:
        title = p.get("title", "")
        path = p.get("path", "").lstrip("/")
        url = p.get("url", "").lstrip("/")

        if (
            title == title_or_path
            or path == search_term
            or url == search_term
            or title_or_path in title
        ):
            post = p
            break

    if not post:
        return f"没有找到标题或路径包含 '{title_or_path}' 的文章"

    title = post.get("title", "")
    content = post.get("content") or post.get("raw") or ""
    url = post.get("url", "")

    return f"文章: {title}\n链接: {url}\n\n内容:\n{content}"
