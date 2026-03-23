"""日志配置模块"""
import logging
import sys
from functools import lru_cache
import httpx


# 配置日志格式
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logger(name: str = "chathexo") -> logging.Logger:
    """设置日志记录器
    
    Args:
        name: 日志记录器名称
        
    Returns:
        配置好的 logger 实例
    """
    logger = logging.getLogger(name)
    
    # 避免重复添加 handler
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    
    # 控制台输出
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # 设置格式
    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    
    return logger


@lru_cache(maxsize=1000)
def get_ip_location(ip: str) -> str:
    """获取 IP 地址的位置信息（带缓存）
    
    Args:
        ip: IP 地址
        
    Returns:
        位置信息字符串，格式：城市, 地区, 国家
    """
    # 跳过本地 IP
    if ip in ["127.0.0.1", "localhost", "::1"]:
        return "local"
    
    try:
        response = httpx.get(f"https://ipinfo.io/{ip}/json", timeout=2.0)
        if response.status_code == 200:
            data = response.json()
            city = data.get("city", "")
            region = data.get("region", "")
            country = data.get("country", "")
            
            parts = [p for p in [city, region, country] if p]
            return ", ".join(parts) if parts else "unknown"
        else:
            return "unknown"
    except Exception:
        return "unknown"


def log_page_visit(
    client_ip: str,
    location: str,
    page_url: str,
) -> None:
    """记录用户访问页面日志

    Args:
        client_ip: 客户端 IP 地址
        location: IP 归属地
        page_url: 用户访问的页面 URL
    """
    logger.info(
        f"Visit | IP: {client_ip} ({location}) | Page: {page_url}"
    )


def log_user_query(
    client_ip: str,
    location: str,
    referer: str,
    model_id: str,
    query: str,
) -> None:
    """记录用户提问日志

    Args:
        client_ip: 客户端 IP 地址
        location: IP 归属地
        referer: 用户当前访问的页面 URL
        model_id: 使用的模型 ID
        query: 用户问题
    """
    logger.info(
        f"💬 Query | IP: {client_ip} ({location}) | "
        f"Page: {referer} | Model: {model_id} | "
        f"Q: {query}"
    )


def get_client_ip(request) -> str:
    """从请求中获取客户端真实 IP
    
    Args:
        request: FastAPI Request 对象
        
    Returns:
        客户端 IP 地址
    """
    # 优先从 X-Forwarded-For 获取（处理代理/负载均衡情况）
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    # 其次从 X-Real-IP 获取
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # 最后使用直连 IP
    return request.client.host if request.client else "unknown"


# 全局 logger 实例
logger = setup_logger()
