"""配置加载模块 - 从 config.json 读取配置"""

from __future__ import annotations

import json
from pathlib import Path
class Settings:
    """配置类 - 从 config.json 读取"""

    def __init__(self):
        # 配置文件在项目根目录的 config/ 文件夹
        config_path = Path(__file__).parent.parent / "config" / "config.json"
        
        if not config_path.exists():
            raise FileNotFoundError(
                f"配置文件不存在: {config_path}\n"
                "请复制 config/config.example.json 为 config/config.json 并填写配置"
            )
        
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        # 服务器配置
        server = config.get("server", {})
        self.host = server.get("host", "127.0.0.1")
        self.port = server.get("port", 4317)
        self.cors_origin = server.get("cors_origin", "*")
        
        # 博客配置
        blog = config.get("blog", {})
        self.posts_dirs_list = blog.get("posts_dirs", [])
        self.index_path = blog.get("index_path", "data/index.json")
        
        # 固定模型配置
        model = config.get("model", {})
        self.model = model.get("name", "gpt-5.6-sol-azure")
        self.base_url = model.get("base_url", "")
        self.api_key = model.get("api_key", "")
        
        # Agent 配置 - 从文件读取系统提示词
        agent = config.get("agent", {})
        prompt_file = agent.get("system_prompt_file", "system_prompt.txt")
        self.system_prompt = self._load_prompt(prompt_file)
    
    def _load_prompt(self, prompt_file: str) -> str:
        """从文件加载系统提示词"""
        # 提示词文件在 config/ 目录
        prompt_path = Path(__file__).parent.parent / "config" / prompt_file
        
        if not prompt_path.exists():
            raise FileNotFoundError(
                f"系统提示词文件不存在: {prompt_path}\n"
                "请确保 config/system_prompt.txt 文件存在"
            )
        
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    
# 全局配置实例
settings = Settings()
