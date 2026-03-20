"""Agent 模块 - 使用 LangGraph Agent 框架"""
from typing import Dict, Any

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver

from chathexo.settings import settings
from chathexo.tools import grep_tool, list_recent_posts, list_all_posts, get_post_content

# 定义要使用的工具列表
TOOLS = [
    grep_tool,
    list_recent_posts,
    list_all_posts,
    get_post_content,
]

# 创建全局 checkpointer
memory = MemorySaver()


def create_my_agent(model_id: str = None):
    """创建 Agent

    Args:
        model_id: 模型ID，如果为None则使用默认模型
    """
    if model_id is None:
        model_id = settings.default_model

    model_config = settings.available_models.get(model_id)
    if not model_config:
        model_id = settings.default_model
        model_config = settings.available_models[model_id]

    llm = ChatOpenAI(
        base_url=model_config["base_url"],
        model=model_config["model"],
        api_key=model_config["api_key"],
        temperature=0.5,
    )

    system_message = settings.system_prompt

    agent = create_agent(
        llm,
        TOOLS,
        system_prompt=system_message,
        checkpointer=memory,
    )

    return agent


def agent_answer(query: str, thread_id: str = "default", model_id: str = None) -> Dict[str, Any]:
    """使用 Agent 回答问题

    Args:
        query: 用户问题
        thread_id: 会话 ID，用于多轮对话
        model_id: 模型ID，用于指定使用的模型
    """
    agent = create_my_agent(model_id)

    try:
        config = {"configurable": {"thread_id": thread_id}}

        state_before = agent.get_state(config)
        messages_count_before = len(state_before.values.get("messages", []))

        result = agent.invoke({"messages": [("user", query)]}, config=config)

        messages = result.get("messages", [])
        answer = messages[-1].content if messages else "没有生成回答"

        new_messages = messages[messages_count_before:]
        tool_calls = []

        for i, msg in enumerate(new_messages):
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    tool_info = {
                        "name": tool_call.get("name", "unknown"),
                        "args": tool_call.get("args", {}),
                        "result": None,
                    }

                    if i + 1 < len(new_messages):
                        next_msg = new_messages[i + 1]
                        if hasattr(next_msg, "content"):
                            tool_info["result"] = next_msg.content

                    tool_calls.append(tool_info)

        return {
            "mode": "agent",
            "answer": answer,
            "tool_calls": tool_calls,
        }
    except Exception as e:
        return {
            "mode": "agent",
            "answer": f"处理问题时出错: {str(e)}",
            "tool_calls": [],
        }
