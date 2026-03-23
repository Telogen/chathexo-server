# ChatHexo Backend

基于 LangGraph Agent 的博客问答助手后端服务。

## 快速开始

### 安装

如未安装 uv 需要先安装 [uv](https://docs.astral.sh/uv/getting-started/installation/)

```bash
# 克隆仓库
git clone https://github.com/Telogen/chathexo-server.git
cd chathexo-server

# 安装依赖
uv sync
```

### 配置

```bash
# 复制配置文件
cp config/config.example.json config/config.json
cp config/system_prompt.example.txt config/system_prompt.txt

# 编辑配置
vim config/config.json
```

主要配置项：

- `blog.posts_dirs`：博客文章目录的绝对路径（如 `/path/to/your-blog/source/_posts`）
- `providers`：填入 API Key 和 base_url（支持 OpenAI 兼容接口）
  - 白嫖 ModelScope API Token 可参考：https://tianlejin.top/blog/claw-daily-ModelScope-Token/
- `models.default`：设置默认模型

### 启动服务

```bash
# 前台运行（开发调试）
uv run python -m chathexo.main

# 后台运行（生产环境）
nohup uv run python -m chathexo.main > /tmp/chathexo.log 2>&1 &
```

服务默认运行在 `http://127.0.0.1:4317`

### 停止服务

```bash
# 查找进程并停止
ps aux | grep "chathexo.main" | grep -v grep | awk '{print $2}' | xargs kill
```


---

## 测试

### 本地测试

```bash
# 健康检查
curl http://127.0.0.1:4317/chathexo-api/health

# 获取可用模型
curl http://127.0.0.1:4317/chathexo-api/models

# 单轮对话
curl -X POST http://127.0.0.1:4317/chathexo-api/chat \
  -H "Content-Type: application/json" \
  -d '{"query":"你好"}'

# 多轮对话
curl -X POST http://127.0.0.1:4317/chathexo-api/chat \
  -H "Content-Type: application/json" \
  -d '{"query":"我叫小明","thread_id":"test123"}'

curl -X POST http://127.0.0.1:4317/chathexo-api/chat \
  -H "Content-Type: application/json" \
  -d '{"query":"我叫什么名字？","thread_id":"test123"}'
```

---

## 与前端集成

### 1. 安装 Hexo 插件

**在 Hexo 博客根目录**：

```bash
npm i hexo-chathexo
```

### 2. 配置 Hexo

编辑 `_config.yml`：

```yaml
chathexo:
  enable: true
  api: /api_chat_hexo/chathexo-api/chat  # 通过 Nginx 代理后的路径
  title: 博客问答
  subtitle: 基于博客知识库的 AI 助手
  assetsPath: chathexo
  indexFile: chathexo/index.json
```

### 3. 配置 Nginx 反向代理

在 Nginx 站点配置中添加：

```nginx
location /api_chat_hexo/ {
    proxy_pass http://127.0.0.1:4317/;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
}
```

重载 Nginx：

```bash
sudo nginx -t && sudo nginx -s reload
```

### 4. 生成博客

```bash
cd your-hexo-blog
hexo clean && hexo generate
```

访问博客，右下角会出现聊天按钮。


### 5. 通过 Nginx 代理测试

```bash
curl -X POST https://your-domain.com/api_chat_hexo/chathexo-api/chat \
  -H "Content-Type: application/json" \
  -d '{"query":"你好"}'
```


---

## 常见问题

### 端口被占用

```bash
# 查找占用进程
lsof -i :4317

# 停止进程
kill <PID>
```

### 修改端口

编辑 `config/config.json`：

```json
{
  "server": {
    "port": 4318
  }
}
```

同时修改 Nginx 配置中的 `proxy_pass` 端口。

### 自定义系统提示词

编辑 `config/system_prompt.txt`，重启服务生效。注意将提示词中的 `your-domain.com` 替换为实际域名。
