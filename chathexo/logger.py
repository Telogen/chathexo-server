"""日志配置模块"""
import logging
import sys
from functools import lru_cache
from typing import Optional
import httpx


# 配置日志格式
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
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
        return "本地"
    
    try:
        # 使用 ipinfo.io API
        response = httpx.get(f"https://ipinfo.io/{ip}/json", timeout=2.0)
        if response.status_code == 200:
            data = response.json()
            city = data.get("city", "")
            region = data.get("region", "")
            country = data.get("country", "")
            
            # 组合位置信息
            parts = [p for p in [city, region, country] if p]
            return ", ".join(parts) if parts else "未知"
        else:
            return "未知"
    except Exception:
        return "未知"


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
