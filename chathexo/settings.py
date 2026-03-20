"""配置加载模块 - 从 config.json 读取配置"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict


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
        
        # Providers 配置
        self._providers = config.get("providers", {})
        
        # 模型配置
        models = config.get("models", {})
        self.default_model = models.get("default", "local-Qwen3.5-35B-A3B")
        self._available_models = models.get("available", {})
        
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
    
    @property
    def available_models(self) -> Dict:
        """可用模型列表 - 自动从 provider 填充 base_url 和 api_key"""
        models = {}
        for model_id, model_config in self._available_models.items():
            config = model_config.copy()
            
            # 获取 provider 配置
            provider_name = config.pop("provider", None)
            if provider_name and provider_name in self._providers:
                provider = self._providers[provider_name]
                config["base_url"] = provider.get("base_url", "")
                config["api_key"] = provider.get("api_key", "")
            else:
                # 如果没有指定 provider 或 provider 不存在，使用默认值
                config.setdefault("base_url", "")
                config.setdefault("api_key", "")
            
            models[model_id] = config
        
        return models


# 全局配置实例
settings = Settings()
