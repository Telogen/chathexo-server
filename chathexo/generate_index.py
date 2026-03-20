"""生成博客索引文件 index.json"""
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import logging

try:
    import yaml
except ImportError:
    yaml = None

# 使用标准 logging
logger = logging.getLogger("chathexo.generate_index")


def clean_content(text: str) -> str:
    """清理 content：移除图片/Hexo 标签，并压缩空白。

    目标：让向量检索的 chunk 更“纯净”，减少 `{% gallery %}` 等噪声对 embedding 的干扰。
    """
    # 移除图片链接 ![alt](url)
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)

    # 移除 HTML img 标签（部分文章用的是 <img ...>）
    text = re.sub(r'<img\b[^>]*>', '', text, flags=re.IGNORECASE)

    # 移除 Hexo 标签块（如 {% gallery %} / {% endgallery %} / {% mermaid %} 等）
    text = re.sub(r'\{%[\s\S]*?%\}', '', text)

    # 移除多余空白行（连续空行压缩为单个空行）
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)

    return text.strip()


def parse_front_matter(content: str) -> tuple[Dict[str, Any], str]:
    """解析 Markdown Front Matter
    
    Returns:
        (front_matter_dict, content_without_front_matter)
    """
    # 匹配 --- 开头和结尾的 YAML Front Matter
    pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
    match = re.match(pattern, content, re.DOTALL)
    
    if not match:
        return {}, content
    
    front_matter_text = match.group(1)
    body = match.group(2)
    
    # 优先使用 PyYAML 解析（更可靠）
    if yaml:
        try:
            front_matter = yaml.safe_load(front_matter_text) or {}
            return front_matter, body
        except Exception as e:
            logger.warning(f"YAML 解析失败，降级为简单解析: {e}")
    
    # 降级：简单解析（保留原逻辑作为兜底）
    front_matter = {}
    current_list_key = None
    
    for line in front_matter_text.split('\n'):
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        
        # 处理 key: value 格式
        if ':' in stripped and not stripped.startswith('-'):
            key, value = stripped.split(':', 1)
            key = key.strip()
            value = value.strip()
            
            if not value:
                # 空值，可能是多行列表的开始
                current_list_key = key
                front_matter[key] = []
            else:
                front_matter[key] = value
                current_list_key = None
        # 处理列表项（- item）
        elif stripped.startswith('-') and current_list_key:
            item = stripped[1:].strip()
            if current_list_key not in front_matter:
                front_matter[current_list_key] = []
            front_matter[current_list_key].append(item)
    
    return front_matter, body


def process_markdown_file(file_path: Path, posts_dir: Path, root_url: str) -> Dict[str, Any]:
    """处理单个 Markdown 文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    front_matter, body = parse_front_matter(content)
    
    # 提取基本信息
    title = front_matter.get('title', file_path.stem)
    abbrlink = front_matter.get('abbrlink', file_path.stem)
    
    # 生成路径和 URL
    relative_path = file_path.relative_to(posts_dir)
    path = f"blog/{abbrlink}.html"
    url = f"/blog/{abbrlink}/"
    
    # 处理日期
    date_str = front_matter.get('date', '')
    updated_str = front_matter.get('updated', date_str)
    
    # 尝试解析日期
    def parse_date(date_str: str) -> str:
        if not date_str:
            return datetime.now().isoformat()
        # 如果已经是 datetime 对象（PyYAML 解析的结果）
        if isinstance(date_str, datetime):
            return date_str.isoformat()
        try:
            # 尝试多种日期格式
            for fmt in ['%Y-%m-%d %H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d']:
                try:
                    dt = datetime.strptime(str(date_str), fmt)
                    return dt.isoformat()
                except ValueError:
                    continue
            # 如果都失败，返回原字符串
            return str(date_str)
        except:
            return datetime.now().isoformat()
    
    date = parse_date(date_str)
    updated = parse_date(updated_str)
    
    # 提取标签和分类（确保是列表）
    tags = front_matter.get('tags', [])
    if isinstance(tags, str):
        tags = [tags]
    elif not isinstance(tags, list):
        tags = []
    
    categories = front_matter.get('categories', [])
    if isinstance(categories, str):
        categories = [categories]
    elif not isinstance(categories, list):
        categories = []
    
    # 构建完整的文章数据（字段顺序：基本信息 → Front Matter 其他字段 → raw/content）
    post_data = {
        'title': title,
        'path': path,
        'source': str(relative_path),
        'abbrlink': abbrlink,
        'url': url,
        'date': date,
        'updated': updated,
        'tags': tags,
        'categories': categories,
    }
    
    # 添加所有其他 Front Matter 字段（如 comments, series, cover 等）
    for key, value in front_matter.items():
        if key not in post_data and key not in ['title', 'date', 'updated', 'tags', 'categories', 'abbrlink']:
            post_data[key] = value
    
    # 最后添加 raw 和 content（raw 在前，content 是 raw 处理后的结果）
    post_data['raw'] = content   # 保留完整原文（包含 Front Matter）
    post_data['content'] = clean_content(body)  # 清理后的正文（移除图片链接）
    
    return post_data


def generate_index(posts_dirs: List[Path], output_path: Path, root_url: str = 'https://www.tianlejin.top'):
    """生成博客索引文件
    
    Args:
        posts_dirs: 文章目录列表，支持多个目录
        output_path: 输出文件路径
        root_url: 博客根 URL
    """
    posts = []
    
    # 遍历所有文章目录
    for posts_dir in posts_dirs:
        if not posts_dir.exists():
            logger.warning(f"目录不存在，跳过: {posts_dir}")
            continue
        
        logger.info(f"扫描目录: {posts_dir}")
        
        # 遍历所有 Markdown 文件
        for md_file in posts_dir.rglob('*.md'):
            # 跳过临时文件和备份文件
            if any(part.startswith('.') for part in md_file.parts):
                logger.debug(f"跳过临时文件: {md_file.relative_to(posts_dir)}")
                continue
            
            try:
                post = process_markdown_file(md_file, posts_dir, root_url)
                posts.append(post)
                logger.info(f"处理文章: {post['title']}")
            except Exception as e:
                logger.error(f"处理文件失败 {md_file.relative_to(posts_dir)}: {e}")
    
    # 按日期倒序排序
    posts.sort(key=lambda p: p.get('date', ''), reverse=True)
    
    # 生成索引数据
    index_data = {
        'generatedAt': datetime.now().isoformat(),
        'site': {
            'title': "Tian Lejin's Site",
            'url': root_url,
            'root': '/'
        },
        'posts': posts
    }
    
    # 写入文件（自定义格式：列表字段不换行）
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 使用自定义格式化
    def format_value(obj, indent=0, parent_key=''):
        """自定义格式化：小列表保持单行，对象和大列表换行"""
        spaces = '  ' * indent
        if isinstance(obj, dict):
            if not obj:
                return '{}'
            lines = ['{']
            items = list(obj.items())
            for i, (k, v) in enumerate(items):
                comma = ',' if i < len(items) - 1 else ''
                if isinstance(v, dict):
                    lines.append(f'{spaces}  "{k}": {format_value(v, indent + 1, k)}{comma}')
                elif isinstance(v, list):
                    # 判断是否是小列表（tags/categories 等）
                    if k in ['tags', 'categories'] or (isinstance(v, list) and len(v) < 20 and all(isinstance(x, (str, int, float, bool, type(None))) for x in v)):
                        # 小列表保持单行
                        lines.append(f'{spaces}  "{k}": {json.dumps(v, ensure_ascii=False)}{comma}')
                    else:
                        # 大列表（如 posts）换行
                        lines.append(f'{spaces}  "{k}": {format_value(v, indent + 1, k)}{comma}')
                else:
                    lines.append(f'{spaces}  "{k}": {json.dumps(v, ensure_ascii=False)}{comma}')
            lines.append(f'{spaces}}}')
            return '\n'.join(lines)
        elif isinstance(obj, list):
            if not obj:
                return '[]'
            # 如果是 posts 这种大列表，每个元素换行
            if parent_key == 'posts':
                lines = ['[']
                for i, item in enumerate(obj):
                    comma = ',' if i < len(obj) - 1 else ''
                    lines.append(f'{spaces}  {format_value(item, indent + 1, parent_key)}{comma}')
                lines.append(f'{spaces}]')
                return '\n'.join(lines)
            else:
                # 其他列表保持单行
                return json.dumps(obj, ensure_ascii=False)
        else:
            return json.dumps(obj, ensure_ascii=False)
    
    formatted_json = format_value(index_data)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(formatted_json)
    
    logger.info(f"完成！共 {len(posts)} 篇文章，输出到: {output_path}")


if __name__ == '__main__':
    # 测试用
    from chathexo.settings import settings
    
    # 项目根目录
    project_root = Path(__file__).parent.parent
    posts_dirs = [Path(d) for d in settings.posts_dirs_list]
    output_path = project_root / settings.index_path
    
    generate_index(posts_dirs, output_path)
