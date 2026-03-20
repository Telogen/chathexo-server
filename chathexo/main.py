"""ChatHexo 后端主程序"""
import uuid
import time
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from chathexo.settings import settings
from chathexo.agent import agent_answer
from chathexo.logger import logger, get_client_ip, get_ip_location


app = FastAPI(title="ChatHexo Backend")


# 日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录所有 HTTP 请求"""
    start_time = time.time()
    
    # 获取客户端 IP 和位置
    client_ip = get_client_ip(request)
    location = get_ip_location(client_ip)
    
    # 记录请求开始
    logger.info(f"请求开始 | {request.method} {request.url.path} | IP: {client_ip} ({location})")
    
    # 处理请求
    response = await call_next(request)
    
    # 计算处理时间
    process_time = time.time() - start_time
    
    # 记录请求完成
    logger.info(
        f"请求完成 | {request.method} {request.url.path} | "
        f"状态: {response.status_code} | 耗时: {process_time:.2f}s | "
        f"IP: {client_ip} ({location})"
    )
    
    return response

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    query: str
    thread_id: str | None = None
    indexUrl: str | None = None
    model: str | None = None  # 新增：指定使用的模型


class ChatResponse(BaseModel):
    mode: str
    answer: str
    thread_id: str
    tool_calls: list = []


@app.get("/chathexo-api/health")
async def health():
    """健康检查"""
    return {"ok": True}


@app.get("/chathexo-api/models")
async def get_models():
    """获取可用模型列表"""
    models = []
    for model_id, config in settings.available_models.items():
        models.append({
            "id": model_id,
            "name": config["display_name"],
        })
    return {
        "models": models,
        "default": settings.default_model,
    }


@app.post("/chathexo-api/chat", response_model=ChatResponse)
async def chat(chat_request: ChatRequest, request: Request):
    """聊天接口"""
    query = chat_request.query.strip()
    if not query:
        return ChatResponse(mode="error", answer="query is required", thread_id="", tool_calls=[])

    thread_id = chat_request.thread_id if chat_request.thread_id else str(uuid.uuid4())
    model_id = chat_request.model if chat_request.model else settings.default_model

    # 获取客户端信息
    client_ip = get_client_ip(request)
    location = get_ip_location(client_ip)
    
    # 记录用户问题
    logger.info(
        f"用户提问 | IP: {client_ip} ({location}) | "
        f"Thread: {thread_id} | Model: {model_id} | "
        f"问题: {query}"
    )

    result = agent_answer(query, thread_id=thread_id, model_id=model_id)
    result["thread_id"] = thread_id

    return ChatResponse(**result)


if __name__ == "__main__":
    # 生成博客索引
    logger.info("开始生成博客索引...")
    from chathexo.generate_index import generate_index

    # 项目根目录
    project_root = Path(__file__).parent.parent
    posts_dirs = [Path(d) for d in settings.posts_dirs_list]
    output_path = project_root / settings.index_path
    generate_index(posts_dirs, output_path)
    logger.info("博客索引生成完成")

    logger.info(f"启动服务: http://{settings.host}:{settings.port}")
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level="info",
        access_log=False,  # 禁用 uvicorn 访问日志，使用自定义日志中间件
    )
