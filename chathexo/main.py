"""ChatHexo 后端主程序"""
import uuid
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict
import uvicorn

from chathexo.settings import settings
from chathexo.agent import agent_answer
from chathexo.logger import logger, get_client_ip, get_ip_location, log_user_query, log_page_visit


app = FastAPI(title="ChatHexo Backend")


# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str
    thread_id: str | None = None
    indexUrl: str | None = None


class ChatResponse(BaseModel):
    mode: str
    answer: str
    thread_id: str
    tool_calls: list = []


@app.get("/chathexo-api/health")
async def health():
    """健康检查"""
    return {"ok": True}


class VisitRequest(BaseModel):
    pageUrl: str


@app.post("/chathexo-api/visit")
async def visit(visit_request: VisitRequest, request: Request):
    """页面访问记录接口"""
    client_ip = get_client_ip(request)
    location = get_ip_location(client_ip)
    log_page_visit(client_ip, location, visit_request.pageUrl)
    return {"ok": True}


@app.post("/chathexo-api/chat", response_model=ChatResponse)
async def chat(chat_request: ChatRequest, request: Request):
    """聊天接口"""
    query = chat_request.query.strip()
    if not query:
        return ChatResponse(mode="error", answer="query is required", thread_id="", tool_calls=[])

    thread_id = chat_request.thread_id if chat_request.thread_id else str(uuid.uuid4())

    # 获取客户端信息
    client_ip = get_client_ip(request)
    location = get_ip_location(client_ip)
    referer = request.headers.get("referer", "unknown")

    # 记录用户问题
    log_user_query(client_ip, location, referer, settings.model, query)

    result = agent_answer(query, thread_id=thread_id)
    result["thread_id"] = thread_id

    return ChatResponse(**result)


if __name__ == "__main__":
    logger.info("Generating blog index...")
    from chathexo.generate_index import generate_index

    project_root = Path(__file__).parent.parent
    posts_dirs = [Path(d) for d in settings.posts_dirs_list]
    output_path = project_root / settings.index_path
    generate_index(posts_dirs, output_path)
    logger.info("Blog index generated")

    logger.info(f"Starting server: http://{settings.host}:{settings.port}")
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level="info",
        access_log=False,  # 禁用 uvicorn 访问日志
    )
